#!/usr/bin/env python3
import argparse
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import signal
import sys

FACILITY = "<14>1"
STOP = False

def handle_sig(sig, frame):
    global STOP
    STOP = True

def iso_local(ts: datetime) -> str:
    return ts.astimezone().isoformat(timespec="microseconds")

def fmt_local_dt(ts: datetime) -> str:
    return ts.astimezone().isoformat(timespec="microseconds")

signal.signal(signal.SIGINT, handle_sig)
signal.signal(signal.SIGTERM, handle_sig)

def fmt_local_dt(ts: datetime) -> str:
    return ts.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    # 서버의 로컬 타임존으로 변환해서 ISO 8601 offset 포함 출력
    # 예: 2026-02-26T17:15:12.892665+09:00
    #return ts.astimezone().isoformat(timespec="microseconds")

def header(ts: datetime, log_type: str, sender_ip: str) -> str:
    return f"{FACILITY} {iso_local(ts)} [{log_type}] [{sender_ip}]"

def append_line(base_dir: Path, filename: str, line: str):
    base_dir.mkdir(parents=True, exist_ok=True)
    with open(base_dir / filename, "a", encoding="utf-8") as f:
        f.write(line + "\n")

@dataclass
class Context:
    users: list[str]
    devices: list[str]
    sender_ips: list[str]
    src_subnets: list[str]
    dst_subnets: list[str]

def rand_ip_from_subnet(subnet_prefix: str) -> str:
    return f"{subnet_prefix}.{random.randint(1, 254)}"

def make_event(ctx: Context, ts: datetime):
    start = ts - timedelta(seconds=random.randint(1, 10))
    end = ts
    user = random.choice(ctx.users)
    machine = random.choice(ctx.devices)
    sender_ip = random.choice(ctx.sender_ips)
    rulename = random.choice(["DDoS_HTTP_Flood","TCP_SYN_Flood","UDP_Flood","DNS_Amplification","Port_Scan","BruteForce_Login"])
    action = random.choice(["탐지","차단"])
    priority = random.randint(0, 3)
    bytes_ = random.randint(1000, 5_000_000)
    packets = random.randint(10, 50000)

    data = (
        f"starttime={fmt_local_dt(start)} "
        f"endtime={fmt_local_dt(end)} "
        f"machine={machine} "
        f"user={user} "
        f"rulename={rulename} "
        f"profile=default "
        f"pdomain=PD#1(default) "
        f"bytes={bytes_} "
        f"packets={packets} "
        f"action={action} "
        f"priority={priority}"
    )
    return sender_ip, header(ts, "event", sender_ip) + " " + data

def make_deny(ctx: Context, ts: datetime):
    user = random.choice(ctx.users)
    machine = random.choice(ctx.devices)
    sender_ip = random.choice(ctx.sender_ips)
    srcip = rand_ip_from_subnet(random.choice(ctx.src_subnets))
    dstip = rand_ip_from_subnet(random.choice(ctx.dst_subnets))
    srcport = random.randint(1024, 65535)
    dstport = random.choice([22, 80, 443, 3389, 5432, 9200])
    protocol = random.choice(["TCP", "UDP"])
    tcpflag = random.choice(["SYN", "ACK", "RST", "PSH", "FIN"]) if protocol == "TCP" else "-"
    ipflag = random.choice(["LAST_FRAG", "NO_FRAG", "FIRST_FRAG"])
    ttl = random.choice([64, 128, 255])
    action = random.choice(["탐지","차단"])
    priority = random.randint(0, 3)
    bytes_ = random.randint(100, 500000)
    packets = random.randint(1, 5000)

    data = (
        f"timestamp={fmt_local_dt(ts)} "
        f"machine={machine} "
        f"user={user} "
        f"rulename=TCP_RST_Flood "
        f"profile=default "
        f"pdomain=PD#1(default) "
        f"srcip={srcip} "
        f"dstip={dstip} "
        f"interface=ETH3(SEG#1-E) "
        f"srcport={srcport} "
        f"dstport={dstport} "
        f"protocol={protocol} "
        f"ipflag={ipflag} "
        f"tcpflag={tcpflag} "
        f"ttl={ttl} "
        f"action={action} "
        f"bytes={bytes_} "
        f"packets={packets} "
        f"priority={priority}"
    )
    return sender_ip, header(ts, "deny", sender_ip) + " " + data

def make_alert(ctx: Context, ts: datetime):
    user = random.choice(ctx.users)
    machine = random.choice(ctx.devices)
    sender_ip = random.choice(ctx.sender_ips)
    alerttype = random.choice(["CPU 과다 사용", "메모리 과다 사용", "로그 저장소 고갈", "비정상적 데몬 종료"])
    alertlevel = random.choice(["Info", "Minor", "Major", "Critical"])
    msg = random.choice(["threshold exceeded","service restarted","disk nearing capacity","unexpected process exit"])

    data = (
        f"timestamp={fmt_local_dt(ts)} "
        f"machine={machine} "
        f"user={user} "
        f"alerttype={alerttype} "
        f"alertlevel={alertlevel} "
        f"msg={msg}"
    )
    return sender_ip, header(ts, "alert", sender_ip) + " " + data

def make_resource(ctx: Context, ts: datetime):
    machine = random.choice(ctx.devices)
    sender_ip = random.choice(ctx.sender_ips)
    core_num = random.choice([4, 8, 16, 32])
    cpu_usage = round(random.uniform(1, 95), 2)
    memtotal = random.choice([8_135_636, 16_271_272, 32_542_544])
    disktotal = random.choice([951_110_868, 1_902_221_736, 3_804_443_472])
    memusage = round(random.uniform(5, 90), 2)
    diskusage = round(random.uniform(1, 80), 2)
    cpu1_temp = random.randint(35, 85)
    cpu2_temp = random.randint(35, 85)

    data = (
        f"timestamp={fmt_local_dt(ts)} "
        f"machine={machine} "
        f"core_num={core_num} "
        f"cpu_usage={cpu_usage} "
        f"memtotal={memtotal} "
        f"disktotal={disktotal} "
        f"memusage={memusage} "
        f"diskusage={diskusage} "
        f"cpu1_temp={cpu1_temp} "
        f"cpu2_temp={cpu2_temp}"
    )
    return sender_ip, header(ts, "resource", sender_ip) + " " + data

GENS = {
    "event": ("event.log", make_event),
    "deny": ("deny.log", make_deny),
    "alert": ("alert.log", make_alert),
    "resource": ("resource.log", make_resource),
}

def main():
    parser = argparse.ArgumentParser(description="UEBA fake log streamer (test scoped)")
    # ⭐️ 수정 2: tenant를 필수가 아닌 선택(default)으로 변경하여 실행 편의성 제공
    parser.add_argument("--tenant", default="test_tenant", help="tenant id (optional)")
    parser.add_argument("--rate", type=float, default=5.0, help="events per second (approx)")
    parser.add_argument("--jitter", type=float, default=0.3, help="sleep jitter ratio (0~1)")
    parser.add_argument("--types", default="event,deny,alert,resource",
                        help="comma-separated types: event,deny,alert,resource")
    # ⭐️ 수정 3: 테스트를 위해 기본 5초만 돌고 멈추도록 설정 (0=forever)
    parser.add_argument("--duration", type=int, default=5, help="seconds to run (0=forever)")
    args = parser.parse_args()

    # ⭐️ 수정 4: 도커 컨테이너 내부의 테스트용 공통 폴더(/app/tests/data/logs)로 고정
    base_dir = Path("/app/tests/data/logs")
    base_dir.mkdir(parents=True, exist_ok=True)

    ctx = Context(
        users=[f"user{n:04d}" for n in range(1, 501)],
        devices=[f"UEBA-MFD-{n:03d}" for n in range(1, 51)],
        sender_ips=[f"192.168.105.{n}" for n in range(10, 31)],
        src_subnets=["10.1.1", "10.1.2", "10.2.1", "172.16.10"],
        dst_subnets=["10.9.1", "10.9.2", "10.10.1", "172.16.20"],
    )

    selected = [t.strip() for t in args.types.split(",") if t.strip()]
    for t in selected:
        if t not in GENS:
            print(f"Unknown type: {t}", file=sys.stderr)
            sys.exit(2)

    ts = datetime.now().astimezone()
    interval = 1.0 / max(args.rate, 0.0001)
    end_time = time.time() + args.duration if args.duration > 0 else None

    while not STOP:
        if end_time is not None and time.time() >= end_time:
            break

        ts = ts + timedelta(milliseconds=random.randint(50, 900))
        t = random.choice(selected)
        filename, fn = GENS[t]
        _, line = fn(ctx, ts)
        append_line(base_dir, filename, line)

        sleep_s = interval * random.uniform(1 - args.jitter, 1 + args.jitter)
        time.sleep(max(0.0, sleep_s))

    print(f"✅ 테스트 로그 생성 완료! 확인 경로: {base_dir}")

if __name__ == "__main__":
    main()