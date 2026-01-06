from flask import Flask
from internal.router import Router
class Http(Flask):
  """
  http 服务引擎
  Http 类继承了 Flask 并且要注册钩子，必须手动写 __init__。
  """

  # *args 是非命名的参数，比如传入 1 'name' false 这种等等
  # **kwargs 是命名的参数，比如传入 name='name' age=18 这种等等
  def __init__(self, *args, router: Router, **kwargs):
    # 使用super去调用父类的构造函数，将整个参数进行实例化。
    # 要不然的话继承别人，如果你不去实现它的构造函数是很容易出错的。 
    super(Http, self).__init__(*args, **kwargs)
    # self.before_request(self.before_request)
    # self.after_request(self.after_request)
    
    # 注册应用路由
    router.register_router(self)