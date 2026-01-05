from injector import Injector, inject


class A:
    name: str = "llmops"


# 想让class B要注入A
class B:
    @inject
    def __init__(self, a: A):
        self.a = a

    def print(self):
        print(f"Class A的name:{self.a.name}")


myInjector = Injector()
b = myInjector.get(B)
b.print()
