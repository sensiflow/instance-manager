from dataclasses import asdict
import json
from typing import Callable, Awaitable

from src.exceptions import AppError
from src.instance_manager.instance.exceptions import (
    InstanceAlreadyExists,
    InstanceNotFound, EndMessageProcessing
)
from src.instance_manager.message import message_dispatcher
from src.instance_manager.message.input_message import InputMessage
from src.instance_manager.message.response_status import ResponseStatus
import logging
from src.instance_manager.message.output_message import CtlAcknowledgeMessage
from instance_manager.message import Action

logger = logging.getLogger(__name__)


class MessageHandler:
    def __init__(
            self,
            delete_queue_name,
            status_queue_name,
            controller_queue_name,
            rabbitmq_client,
            instance_service
    ):
        self.delete_queue_name = delete_queue_name
        self.status_queue_name = status_queue_name
        self.controller_queue_name = controller_queue_name
        self.rabbitmq_client = rabbitmq_client
        self.instance_service = instance_service
        self.instance_ack_exchange_name = "instance_ack_exchange"

    async def send(
            # TODO: do not use action to diferentiate the queues,  use just one queue and use the status to diferentiate what to do
            self,
            response_message,
            response_status,
            device_id: int,
            action: Action
    ):
        """
            Sends a message to the RabbitMQ queue.
            Parameters:
                response_message: message to be sent.
                response_status: status of the message.
                device_id: device id of the message.
                action: action that was executed on the instance.
        """
        routing_key = self.delete_queue_name \
            if action.value == Action.REMOVE.value \
            else self.status_queue_name

        action_name = action.name if action else None

        ack_message = CtlAcknowledgeMessage(
            code=self.__message_code_mapper(response_status),
            device_id=device_id,
            action=action_name,
            message=response_message
        )

        await self.rabbitmq_client.send_message(
            routing_key=routing_key,
            exchange_name=self.instance_ack_exchange_name,
            message=asdict(ack_message)
        )

    async def __process_unique_message(
            self,
            input_message: InputMessage,
    ):
        """
            Function use for processing messages that are unique to an instance.
        """
        await message_dispatcher(input_message, self.instance_service)

    async def __process_shared_message(
            self,
            input_message: InputMessage,
            device_id: int,
            onACK: Callable[[], Awaitable[None]]
    ):
        """
            Function use for processing messages that are shared between other instances.
        """
        if not await self.instance_service.validate_instance(device_id):
            # Discard message if the instance does not exist, but send ack anyway, this message is not for us
            logger.warning("Instance does not exist. Discarding message...")
            await onACK()
            raise EndMessageProcessing()

        await message_dispatcher(input_message, self.instance_service)

    async def process_shared_messages(
            self,
            received_message):
        await self._process_message(received_message, True,)

    async def process_unique_messages(
            self,
            received_message):
        await self._process_message(received_message, False)

    async def _process_message(
            self,
            received_message,
            is_shared: bool = False
    ):
        """
            Callback function for processing received messages from RabbitMQ.
            Parameters:
                received_message: message received from RabbitMQ.
        """
        logger.info("Starting to process message...")
        try:
            input_message = self.__build_message_dto(received_message)
            device_id = input_message.device_id
            action = input_message.action

            if not is_shared:
                await self.__process_unique_message(input_message)
            else:
                try:
                    await self.__process_shared_message(input_message, device_id, received_message.ack)
                except EndMessageProcessing:
                    return

            await self.send(
                response_status=ResponseStatus.Ok,
                response_message="OK",
                device_id=device_id,
                action=action
            )
            await received_message.ack()
        except (KeyError, json.decoder.JSONDecodeError):
            # Discard message if it hasn't the required format
            logger.warning("Invalid message format. Discarding message...")
            await received_message.ack()
        except AppError as e:
            await self.send(
                response_status=self.__app_error_status_mapper(e),
                response_message=e.message,
                device_id=device_id,
                action=action
            )
            await received_message.ack()
        except Exception:
            logger.exception("Unexpected error.")
            await received_message.reject(requeue=False)

    def __build_message_dto(self, input_message) -> InputMessage:
        """
            Builds a InputMessage object from the received message.
            Parameters:
                input_message: message received from RabbitMQ.
            Returns:
                InputMessage object.
        """
        message_body = input_message.body.decode()
        message_dict = json.loads(message_body)

        message_dto = InputMessage(
            action=Action[message_dict["action"]],
            device_id=message_dict["device_id"],
            device_stream_url=message_dict.get("device_stream_url")
        )

        logger.info(f"Received message: {message_dto}")
        return message_dto

    def __message_code_mapper(self, status):
        mapper = {
            ResponseStatus.Ok: 2000,
            ResponseStatus.BadRequest: 4000,
            ResponseStatus.NotFound: 4004,
            ResponseStatus.Conflict: 4009,
            ResponseStatus.InternalError: 5000,
            ResponseStatus.InconsistentContainerState: 5001
        }
        return mapper[status]

    def __app_error_status_mapper(self, error):
        mapper = {
            InstanceNotFound: ResponseStatus.NotFound,
            InstanceAlreadyExists: ResponseStatus.Conflict
        }
        return mapper[error.__class__]
