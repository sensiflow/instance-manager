from dataclasses import asdict
import json
from src.exceptions import AppError
from src.instance_manager.instance.exceptions import (
    InstanceAlreadyExists,
    InstanceNotFound
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
            status_queue_name,
            controller_queue_name,
            rabbitmq_client,
            instance_service
    ):
        self.status_queue_name = status_queue_name
        self.controller_queue_name = controller_queue_name
        self.rabbitmq_client = rabbitmq_client
        self.instance_service = instance_service
        self.instance_ack_exchange_name = "instance_ack_exchange"

    async def send(
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
        action_name = action.name if action else None

        ack_message = CtlAcknowledgeMessage(
            code=self.__message_code_mapper(response_status),
            device_id=device_id,
            action=action_name,
            message=response_message
        )

        await self.rabbitmq_client.send_message(
            routing_key=self.status_queue_name,
            exchange_name=self.instance_ack_exchange_name,
            message=asdict(ack_message)
        )

    async def process_message(
            self,
            received_message
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

            await message_dispatcher(input_message, self.instance_service)

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
