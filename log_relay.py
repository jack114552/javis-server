"""日志中继 — OpenCode 把输出发到这里，小千可以从这里读"""
import sys
from pathlib import Path
from datetime import datetime

LOG_FILE = Path('/opt/javis/logs/opencode.log')

def main():
    if len(sys.argv) < 2:
        print('用法: log_relay.py "消息内容"')
        sys.exit(1)
    msg = sys.argv[1]
    ts = datetime.now().strftime('%H:%M:%S')
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'[{ts}] {msg}\n')
    lines = LOG_FILE.read_text(encoding='utf-8').splitlines()
    if len(lines) > 500:
        LOG_FILE.write_text('\n'.join(lines[-500:]), encoding='utf-8')
    print('ok')

if __name__ == '__main__':
    main()
