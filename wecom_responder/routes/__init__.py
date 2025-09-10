# # 为了向后兼容，导出一些常用的bp变量
# def get_bp(package_name: str, bp_name: str = None):
#     """获取bp的辅助函数"""
#     return bp_loader.get_bp_by_name(package_name, bp_name)

# 常用bp的快捷访问
# bp_verify = get_bp('verify')
# bp_redirectlocal = get_bp('redirectlocal')
# bp_root = get_bp('root')

# 如果需要获取特定bp，可以使用：
# bp_recv_from_subscribe_chan = get_bp('subscribe_chan', 'subscribe_chan_recv')
# bp_send_to_subscribe_chan = get_bp('subscribe_chan', 'subscribe_chan_send')

# 导出加载器和已加载的bp字典
# __all__ = ['bp_loader', 'loaded_bps', 'get_bp']