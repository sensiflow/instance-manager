from src.exceptions import AppError


class InstanceNotFound(AppError):
    def __init__(self, instance_id):
        self.message = f"Instance with id {instance_id} not found"
        super().__init__(self.message)


class InstanceAlreadyExists(AppError):
    def __init__(self, instance_id):
        self.message = f"Instance with id {instance_id} was already created."
        super().__init__(self.message)


class EndMessageProcessing(AppError):
    def __int__(self):
        self.message = "End message processing"
        super().__init__(self.message)


class InternalError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DomainLogicError(Exception):
    pass
