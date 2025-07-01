from backend.utils.singleton import Singleton

def test_singleton_instance():
    @Singleton
    class MySingleton:
        def __init__(self, value):
            self.value = value
    instance1 = MySingleton(42)
    instance2 = MySingleton(99)
    
    assert instance1 is instance2
    assert instance1.value == 42
    assert instance2.value == 42

def test_multiple_singleton_instance():
    @Singleton
    class MySingleton1:
        def __init__(self, value):
            self.value = value
    @Singleton
    class MySingleton2:
        def __init__(self, value):
            self.value = value
    instance1 = MySingleton1(42)
    instance2 = MySingleton2(99)
    instance3 = MySingleton1(100)
    instance4 = MySingleton2(200)

    assert instance1 is instance3
    assert instance2 is instance4
    assert instance1.value == 42
    assert instance2.value == 99
    assert instance1 is not instance2