class IncompatibleConfigVariables(Exception):
    def __init__(self, env_var1, env_var2):
        self.message = f"""
            Environment variables {env_var1} and {env_var2} are incompatible
        """
        super().__init__(self.message)


class GoalTimeout(Exception):
    def __init__(self, container_name):
        self.message = f"""
            Container {container_name} did not reach goal in time
        """
        super().__init__(self.message)
