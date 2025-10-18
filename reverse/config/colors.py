from reverse.structure.singleton import Singleton


class Colors(Singleton):
    def __init__(self) -> None:
        self.__red = 0xDC143C
        self.__green = 0x1F8B4C
        self.__grey = 0x708090
        self.__blue = 0x206694
        self.__black = 0x23272A
        self.__log = 0xd51a65
        self.__yellow = 0xffb800
        self.__invis = 0x2F3136

    @property
    def red(self) -> int:
        return self.__red

    @property
    def green(self) -> int:
        return self.__green

    @property
    def grey(self) -> int:
        return self.__grey

    @property
    def blue(self) -> int:
        return self.__blue

    @property
    def black(self) -> int:
        return self.__black

    @property
    def log(self) -> int:
        return self.__log

    @property
    def yellow(self) -> int:
        return self.__yellow

    @property
    def invis(self) -> int:
        return  self.__invis