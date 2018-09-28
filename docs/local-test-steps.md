## 启动测试节点

```bash
docker run --rm -d --name neo-privatenet -p 20333-20336:20333-20336/tcp -p 30333-30336:30333-30336/tcp cityofzion/neo-privatenet

```

## 启动测试命令行客户端

```bash
cd neo-python
source venv/bin/activate
np-prompt -p
```

## 编译部署测试合约

```bash
# 编译
build test_contract.py test 0710 05 False False False sell [b'from', b'asset', 0x1234]

# 部署
import contract test_contract.avm 0710 05 False False False
```

## 调用合约

```bash
# 注意这里的 hash 是上一步产生的 hash
testinvoke 0xcfdff42a0fa99aeee31e2af5e140e0f9040b5d46 sell [b'from', b'asset', 0x1234]

# 如果调用不成功，可以尝试先运行 `wallet rebuild` 然后在重新执行部署后再调用
```