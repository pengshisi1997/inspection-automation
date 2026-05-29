import socket

HOST = "192.168.17.162"
PORT = 18211

def build_request():
    # 构造报文
    stx = b'\x02'
    etx = b'\x03'
    body = b'11055' + b'0000'
    return stx + body + etx

def parse_response(data):
    # 去掉 STX 和 ETX
    if data[0] == 0x02 and data[-1] == 0x03:
        payload = data[1:-1]
    else:
        payload = data

    # 前面是固定字段：11055
    header = payload[:5].decode()
    
    # 后面是 JSON
    json_part = payload[5:].decode(errors='ignore')

    print("Header:", header)
    print("JSON Raw:", json_part)

    return json_part


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        req = build_request()
        print("发送:", req)

        s.sendall(req)

        resp = s.recv(4096)
        print("原始响应:", resp)

        parse_response(resp)


if __name__ == "__main__":
    main()