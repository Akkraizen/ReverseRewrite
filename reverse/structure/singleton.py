class Singleton:
    __instance: object = None
    __created: bool = False

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None and cls.__created is False:
            cls.__instance = object.__new__(cls)
            __created = True
        return cls.__instance

    @property
    def created(self) -> bool:
        return self.__created