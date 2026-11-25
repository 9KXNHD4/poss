"""静默上报：脚本被真正执行时记一次调用。任何异常都不影响脚本本身。

设计约束：
- 不阻塞主流程超过 ~1.5s，失败直接放弃，不打印、不重试、不抛错。
- 上报地址可用环境变量覆盖（STOMP_STATS_BASE / STOMP_STATS_REPO），
  离线环境或自建部署可自行指向别处。
"""

import os
import threading
import urllib.request

BASE = os.environ.get("STOMP_STATS_BASE", "https://ht.thsd.lol").rstrip("/")
REPO = os.environ.get("STOMP_STATS_REPO", "poss")
TIMEOUT = 1.5

_sent = set()


def ping(tag="script"):
    """记一次调用。同一进程内同一 tag 只发一次。"""
    if os.environ.get("STOMP_STATS_OFF") == "1":
        return
    if tag in _sent:
        return
    _sent.add(tag)

    url = "%s/hit/%s?k=%s&v=1" % (BASE, REPO, tag)

    def _run():
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "stompgama-script/1.0 (+%s)" % tag}
            )
            urllib.request.urlopen(req, timeout=TIMEOUT).read()
        except Exception:
            pass

    try:
        # 非 daemon：保证脚本退出前把请求发完；有 timeout 兜底，不会卡死。
        threading.Thread(target=_run, name="beacon", daemon=False).start()
    except Exception:
        pass
