class IncompatibleConfigVariables(Exception):
    def __init__(self, env_var1, env_var2):
        self.message = f"""
            Environment variables {env_var1} and {env_var2} are incompatible
        """
        super().__init__(self.message)


class ContainerExitedError(Exception):
    """
    Raised when a container exits unexpectedly without reaching its goal
    """

    def __init__(self, container_name, error_message):
        self.message = f"""
            Container {container_name} exited, error: {error_message}
        """
        super().__init__(self.message)


class ContainerGoalTimeout(Exception):
    def __init__(self, container_name):
        self.message = f"""
        Container {container_name} did not reach goal in time
        """
        super().__init__(self.message)


class ContainerNotFound(Exception):
    def __init__(self, container_name):
        self.message = f"""
            Instance was created but the container {container_name} \
            does not exist.
        """
        super().__init__(self.message)
