
class InstanceNotFound(Exception):
    def __init__(self, instance_id: str):
        message = f"""
            Instance with id {instance_id} not found
        """
        super().__init__(message)
        pass


class DomainLogicError(Exception):
    pass
