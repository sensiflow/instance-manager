class IncompatibleConfigVariables(Exception):
    def __init__(self, env_var1, env_var2):
        self.message = f"""
            Environment variables {env_var1} and {env_var2} are incompatible
        """
        super().__init__(self.message)
