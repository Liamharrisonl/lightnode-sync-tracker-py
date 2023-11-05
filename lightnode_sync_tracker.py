#!/usr/bin/env python3
import os, sys, time, json
import urllib.request

RPC = os.getenv("ETH_RPC", "https://rpc.ankr.com/eth")
POLL = float(os.getenv("POLL", "8"))

def rpc(method, params=None, timeout=8):
    req = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params or []}).encode()
    with urllib.request.urlopen(urllib.request.Request(RPC, data=req, headers={"content-type":"application/json"}), timeout=timeout) as r:
        data = json.load(r)
        if "error" in data: raise RuntimeError(data["error"])
        return data["result"]

def hex_to_int(x): return int(x, 16) if isinstance(x,str) and x.startswith("0x") else int(x or 0)

def main():
    print(f"Using ETH RPC: {RPC}")
    # moving averages to smooth noise
    lag_ema, speed_ema = None, None
    last_block, last_t = None, None

    while True:
        try:
            head_hex = rpc("eth_blockNumber")
            head = hex_to_int(head_hex)

            sync = rpc("eth_syncing")
            if sync is False:
                local = head
                phase = "synced"
            else:
                local = hex_to_int(sync.get("currentBlock","0x0"))
                phase = "catching-up"

            now = time.time()
            if last_block is not None:
                dt = max(now - last_t, 1e-6)
                speed = (local - last_block) / dt
                speed_ema = speed if speed_ema is None else speed_ema*0.8 + speed*0.2
            lag = head - local
            lag_ema = lag if lag_ema is None else int(lag_ema*0.7 + lag*0.3)

            print(f"[{time.strftime('%H:%M:%S')}] phase={phase:11} head={head} local={local} lag={lag_ema} ~speed={speed_ema:.2f} blk/s")
            last_block, last_t = local, now
        except Exception as e:
            print("warn:", e)

        time.sleep(POLL)

if __name__ == "__main__":
    main()
