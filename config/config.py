class Config:
  def __init__(self):
    # 关闭WTF的CSRF保护
    self.WTF_CSRF_ENABLED = False