from boa.interop.Neo.Runtime import Notify


def Main(operation, args):
    n_args = len(args)

    if n_args == 0:
        print('no method')
        return 0

    if operation == 'sell':

        if n_args != 3:
            print('missing params')
            return 0

        from_addr = args[0]
        asset = args[1]
        price = args[2]
        return Sell(from_addr, asset, price)

    return 0


def Sell(from_addr, asset, price):
    # 和 solidity 不一样，neo 事件只支持单参数，所以多参数采用数组包裹
    Notify([from_addr, asset, price])
    # 测试 neo 的大小端序
    return 0x1234
