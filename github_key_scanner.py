#!/usr/bin/env python3
#
# ╔══════════════════════════════════════════════════════════╗
# ║  r5hhhh2ssi;;iiiiiiiiii;r2hMMMMMMMMMMMMMhhhh5r;ii;;;;; ║
# ║  A233hhhh3Arrrrsiiiiiii2hMMMMhhMMMMMMMMMhhhhMMA;;;;;;; ║
# ║  A25555333552AXAsiiiir3MMhMMhhMMMMhhMMMMMMMMhhM5ii;;; ║
# ║  A22255555352AXXriiirhMhMMhhhMMMMMMhhMMhMMMMMMhM2iiii ║
# ║  ssssXsirsrrrrrrrrrsM3hMM3h3MhMMhMMM3hMh3MMMhhMMMhri ║
# ║  irrrrrrrrrrrrrrrriXh3MMhhh5M2hhh3MM53h53hMMhhhMMMXr ║
# ║  rrrrrrrrrrrrrrrrrrshhMH33h3hA52M5hH22hA33hhhhhhMM3h ║
# ║  rrrrrrrrrrrrrrrrrrA33HM253h53AXA32MAX223555Mhh3M3MS ║
# ║  rrrrrrrrrrrrrrrrrr3X3h33SSH3iH#9GhAhS9h;MHGM33hH3MM ║
# ║  rrrrrrrrrrrsssAAssssrr2hM3hG#99#9#H9####9SMh33523MG ║
# ║  srrsXXXXsXA553MhMHHHH2XAAAX2MS9###S##9#G5XsXsA5HSG ║
# ║  s222hG##MHSSSSSSGSSSGH2MAsAAX3S999999#G2XX2sAMHHHG ║
# ║  5HGGGS#9#SS##SS#####SSGGG5AMAs3MH##SHGG35Hh3MMMHHH ║
# ║  MHGSSS999##99#SSSSS#SGSSSSHMhh3M353HS9GH#9S#GhhMMH ║
# ║  GGSSSS##9####SSSSSSSSGGGGGGHHMh#SGS999SHSS###GMMHH ║
# ║  GGGGGGGGGGGGGGSSSSSSSSSSGGHGHM#9999#999GHSSGGSGGGH ║
# ║  HHHMHHHGGGGGGGGGHHHHMMMMS#99GMG#9999#SS9B&B9SHMhMM ║
# ║  hhhhhhhhhhhhhhh333hhHG3H9&&B&&#SG#9SS9B&&&&&GH9Gh3 ║
# ║  GitHub AI Credential Leak Scanner  v2 ║
# ╚══════════════════════════════════════════════════════════╝
"""
GitHub AI Credential Leak Scanner v2
═══════════════════════════════════════
GitHub 公开仓库 AI API 密钥泄露扫描器 — 覆盖 30+ 服务商
支持高熵检测、分级统计、Markdown 报告

用法:
    python github_key_scanner.py                       # 无 token
    python github_key_scanner.py --token ghp_xxx       # 有 token 加速
    python github_key_scanner.py --token ghp_xxx --entropy  # +高熵模式
    python github_key_scanner.py --token ghp_xxx --deep    # 深度扫描(46搜索词)

Token: https://github.com/settings/tokens -> classic -> public_repo
"""

import subprocess as _sp, sys as _sys, importlib as _il

try:
    import requests  # type: ignore
except ImportError:
    requests = None

import json, re, os, time, hashlib, argparse, sys, math
from urllib.parse import quote
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError
from collections import defaultdict, Counter
from datetime import datetime

class _CompatResponse:
    def __init__(self, status_code, text='', headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def json(self):
        return json.loads(self.text) if self.text else {}


class _CompatSession:
    def __init__(self):
        self.headers = {}
        self._opener = build_opener()

    def get(self, url, timeout=25):
        req = Request(url, headers=dict(self.headers), method='GET')
        try:
            with self._opener.open(req, timeout=timeout) as resp:
                data = resp.read()
                encoding = resp.headers.get_content_charset() or 'utf-8'
                text = data.decode(encoding, errors='replace')
                return _CompatResponse(resp.status, text, dict(resp.headers.items()))
        except HTTPError as e:
            data = e.read() if hasattr(e, 'read') else b''
            encoding = None
            try:
                encoding = e.headers.get_content_charset()
            except Exception:
                pass
            text = data.decode(encoding or 'utf-8', errors='replace') if data else ''
            return _CompatResponse(getattr(e, 'code', 0) or 0, text, dict(getattr(e, 'headers', {}).items()) if getattr(e, 'headers', None) else {})
        except URLError:
            return None
        except Exception:
            return None


if requests is None:
    class _RequestsCompat:
        Session = _CompatSession
    requests = _RequestsCompat()

import shutil

STARTUP_ANIMATION_SECONDS = 4.0
STARTUP_FRAME_DELAY = 0.12
STARTUP_FRAMES = [
    r"""s3hhhAXi;iriiiii;iAhMMMMMMMMMMhhh3s;ii;;;;;;;;;issriii
A5333h32XsXsiii;XhMMMhhMMMhMMMMMhMM2;;;;;iirssXA2Xrrii
A25555535AXXriiAMhMMhhMMMMhhMhMMMMMM2iiiirsA5555Ariiii
AAAAXsA2ArririsMhMMhhMhMMMMhMhhMMhMMMXiirXA5222Xsiiiii
rrrsrrrrrrrrri2hhMh3hhhMhMM3hh3MMhhMMhirsXA2AAXAsriiii
rrrrrrrrrrrrriAhMM3h3323h3H2353hhhhhMM5532XXAsrrriiiii
rrrrrrrrrrrrrr23Mh23h32s22hXA23553hhh3GGHM32Arrrrrrrii
rrrrrrrrrrrrrs52M5hHMA5MM2X2h3s33333M3HHHHhXrrrrrrrrsX
rrrrrrrrrrrrrs2Ah3h##MMB99HS9#3##Hh3MhMMH3Xrrrrrrrs3MH
rrrrrsssssAXsssrAhhhS99##G#9##9Gh3355MGHMAXXXAAAXsAhhM
srrsrrrrsA23h335Xs225M#9#HS###S3AXsX3SSGMMGGHHGHMh2553
sAX5hM5hHHGGHGSGM22sXAh#99#99S3sXsAMHGGGHHHHHGSSGGh225
5HGG#9####S####SSGS353X3HGSGGG33M3MMHHHHHMMHGGSSSSGGH3
HGSS#99#99#SSSSSGGSSHMh3H3hG9SH###GhhMHS#GHGSGHGGGSSSM
GSGGGSSSSSSSSSSSSSGGHHMG9#999#HGSS#GHGHGSSGGGGMMMHGGGG
HHHHHGHHGGGGHHHMMMG###HG#99####BB9GHMMMMMMMMMMMMMMMMMM
h33hhhhhhh333hhGShG&&&&B9##9B&&&&BM##Hh33333333333hhhh
333333555535553hhHhG##B9SH2MH#BShHhhhh5255355555555553
5555555555AAA22AAGHAAMGA;iX;;sMG5G5AAAAAAA533555555555
5533333335H9hA22AhG5AS3;hA#sh53HHhA222AAM9h3h3h333h333
AAAAAAAAAA9&&#3sA5G3h5M9h5@A2MhSGA22AX5#&&GXAAAAAA2222
rrrrrrrrrXBBB&92A2SHh3M9sH@5X3H9hA22AhB&BB#srrrrrrrrrr""",
    r"""s3hhhAXi;iiiiiii;iAhMMMMMMMMMMhhM3s;;i;;;;;;;;;issriii
A533hhh2XsXsiii;XhMMMhhMMMhMMMMMhMM2;;;;;iirsssA2Xrrii
A22555535AXXriiXMhMMhhMMMMhhMhMMMMMH2iiiirsA5555Ariiii
AAAAXsA2ArrrrisMhMMhhhhMMMMhMhhMMhMMMXiirsA5222Xsiiiii
rrrsrrrrrrrrriAhhMh33hhMhMM3hh3MMhhMMhiisXA2AAXAsriiii
irrirrrrrrrrriAhMM3h3323h3H2355hhhhhMM5532XXXsrrriiiii
rrrrrrrrrrrrrr23Mh23h32s22hXA23253hhh3HGHM32Arrrrrrrii
rrrrrrrrrrrrrs52M5hHMA2MM2X2h3s33333M3HHHHhXrrrrrrrrsX
rrrrrrrrrrrrrs2Ah3h##MM999HS9#3##Hh3MhMMH3Xrrrrrrrs5MH
rrrrrsssssAXsssrAhhhS99##G#9##9Gh3355MGHMAXXXAAXXsAhhM
srrsrrrrXA23h355XX222M#9#HS###S3AXsX3SSGMMGGHHGHMh2553
sXX5hM53HHGGHGSGM22sXAh#99#99S3sXsAhHGGGHHHHHGSSGGh225
5HGG#9####S####SSGS353X3HGSGGG53M3MHHHHHHMMHGGSSSSGGH3
HGSS##9#99#SSSSSGSSSHMh3H3hG9SH###GhMMHS#GHGSGHGGGSSSh
GGGGSSSSSSSSSSSSSGGGHHHG9##99#HGSS#GHGHGSSGGGGMMMHGGGG
HHHHHGHHGGGGHHHMMHG#9#HG9#MH###BB#GHMMMMMMMMMMMMMMMMMM
h3hhhhhhhhh333hG#B&@&&&BShhMGB&&&@@&#Hh333333333hhhhhh
333333555535555hMHGS#9&9GMGGS#&9GHHMhh5255555555555553
5555555553AAA22AAAAAAHHXHHMGGM3hXAAAAAA2AA535555555555
5533333335M9hAA222222XisHSMMSM22222222AAM9h3h3h33hh333
AAAAAAAAAX#&&#3s2222A5GGh3GG#9HA22A2AX5S&&HXAAAAAA2225
rrrrrrrrrs9&B&BAA2222AH9M35H99HA2222AMB&BB9srrrrrrrrrr""",
    r"""s3hh3AXi;iiiiiii;iAhMMMMMMMMMMMhh3s;;i;;;;;;;;;issriii
A5533h32XsXsiii;XhMMMhhMMMhMMMMMhMM2;;;;;iirXsXA2Xriii
A25555535AXXriiAMhMMhhMMMMhMMhMMMMhM2iiiirsA5555Ariiii
AAAAXXA2ArrrrisMhMMhhhMMMMMhMhhMMhMMMXiirX25222Xsiiiii
rrrsrrrrrrrrri2hhMh33hhMhMM3hh3MMhhMMhirsXA2AAXXsriiii
rrrrrrrrrrrrriAhMM3h3323h3H2353hhhhhMM5532XXAsrrriiiii
rrrrrrrrrrrrrr23Mh23h32s22hXA23253hhh3GGHM32Arrrrrrrii
rrrrrrrrrrrrrs52M5hHMA5MM2X2h3s33333M3HHHHhXrrrrrrrrsX
rrrrrrrrrrrrrs2Ah3h##MM999HS9#3##Hh3MhMMH3Xrrrrrrrs3MH
rrrrrsssssAXsssrAhhhS99##G#9##9Gh3325MGHMAXXXAAXXsAhhM
srrsrrrrXA23h355Xs225M#9#HS###S3AXsX3SSGMMGGHHGHMh2553
sXX5hM53HHGGHGSGM22sXAh#99#99S3sXsAMHGGGHHHHHGSSGGh225
5HGG#9####S####SSGG353X3HGSGGG53M3MMHHHHHMMHGGSSSSGGH3
HGSS#99#99#SSSSSGGSSHMh3H3hG9SH9##GhhMHS#GHGSGHGGGSSSM
GSGGSSSSSSSSSSSSSSGGHHMG9#999#HGS##GHGHGSSGGGGMMMHGGGG
HHHHHGHHGGGGHHHMMMH#9#HG#99####B&SMHMMMMMMMMMMMMMMMMMM
h3hhhhhhhh3333hG#MHB@&&B###9BB&BGGH&#Hh33333333333hhhh
333333555535553hMMGH##B9SM2MGSGHMGMMhh5255355555555553
5555555553AAA22AA3S3M3MX;iX;;sG5GG5XAAAAA2533555555555
5533333335H9hA2223G2GH;rhA#sMshGHHA222AAHBh3hh3333h333
AAAAAAAAXAB&&#5s2Ghh33MB32@sH9AMGG22AX3#&&HsAAAAAA2225
rrrrrrrriXBBB&#22#Ghh3H&rH@2AM2h#SAA2hB&BB#srrrrrrrrrr"""
]


def autoplay_startup_gif():
    try:
        if not STARTUP_FRAMES:
            return
        loops = max(1, int(STARTUP_ANIMATION_SECONDS / STARTUP_FRAME_DELAY / len(STARTUP_FRAMES)))
        _sys.stdout.write('\x1b[2J\x1b[H\x1b[?25l')
        _sys.stdout.flush()
        try:
            for _ in range(loops):
                for frame in STARTUP_FRAMES:
                    _sys.stdout.write('\x1b[H')
                    _sys.stdout.write(frame)
                    _sys.stdout.write('\n')
                    _sys.stdout.flush()
                    time.sleep(STARTUP_FRAME_DELAY)
        finally:
            _sys.stdout.write('\x1b[2J\x1b[H\x1b[?25h')
            _sys.stdout.flush()
    except Exception:
        pass

# ═══════ ANSI ═══════
class C:
    R='\033[91m';G='\033[92m';Y='\033[93m';B='\033[94m';M='\033[95m';C='\033[96m';W='\033[97m';D='\033[90m'
    BOLD='\033[1m';RESET='\033[0m'
def dim(s):return f'{C.D}{s}{C.RESET}'
def bold(s):return f'{C.BOLD}{s}{C.RESET}'
def red(s):return f'{C.R}{s}{C.RESET}'
def green(s):return f'{C.G}{s}{C.RESET}'
def cyan(s):return f'{C.C}{s}{C.RESET}'
def yellow(s):return f'{C.Y}{s}{C.RESET}'

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════ 搜索词 ═══════
SEARCH_DEEP = [
    'filename:.env OPENAI_API_KEY',
    'filename:.env DEEPSEEK_API_KEY',
    'filename:.env ANTHROPIC_API_KEY',
    'filename:.env GOOGLE_API_KEY',
    'filename:.env DASHSCOPE_API_KEY',
    'filename:.env ZHIPUAI_API_KEY',
    'filename:.env MOONSHOT_API_KEY',
    'filename:.env GROQ_API_KEY',
    'filename:.env HUGGINGFACE_TOKEN',
    'filename:.env COHERE_API_KEY',
    'filename:.env MISTRAL_API_KEY',
    'filename:.env REPLICATE_API_TOKEN',
    'filename:.env PERPLEXITY_API_KEY',
    'filename:.env BAICHUAN_API_KEY',
    'filename:.env VOLCENGINE_API_KEY',
    'filename:.env MINIMAX_API_KEY',
    'filename:.env STEPFUN_API_KEY',
    'filename:.env HUNYUAN_API_KEY',
    'filename:.env TOGETHER_API_KEY',
    'filename:.env XAI_API_KEY',
    'filename:.env "api_key"',
    'filename:.env.local "api_key"',
    'filename:env OPENAI_API_KEY',
    'filename:config.json "api_key"',
    'filename:config.yaml api_key',
    'filename:config.py api_key',
    'filename:settings.py api_key',
    'filename:secrets.yaml api_key',
    'filename:credentials.json api_key',
    '"OPENAI_API_KEY" "sk-" language:python',
    '"DEEPSEEK_API_KEY" "sk-" language:python',
    '"ANTHROPIC_API_KEY" "sk-ant" language:python',
    '"GOOGLE_API_KEY" "AIza" language:python',
    '"DASHSCOPE_API_KEY" "sk-" language:python',
    '"GROQ_API_KEY" "gsk_" language:python',
    '"OPENAI_API_KEY" "sk-" language:javascript',
    '"DEEPSEEK_API_KEY" "sk-" language:typescript',
    'one-api sk- filename:env',
    'new-api sk- filename:env',
    'channel sk- filename:json',
    'OPENAI_API_KEY DEEPSEEK_API_KEY path:.env',
    'filename:.github OPENAI_API_KEY',
    'filename:docker-compose.yml api_key',
    'filename:Dockerfile api_key',
    'filename:Makefile api_key',
]
SEARCH_FAST = SEARCH_DEEP[:12]

# ═══════ 密钥正则 — 精确匹配(无变宽look-behind) ═══════
# 分两步: 1) 宽正则全量提取  2) classify_key 精确归类
KEY_REGEX = re.compile(
    r'sk-proj-\w{60,}'                              # OpenAI proj
    r'|sk-svcacct-\w{60,}'                          # OpenAI svc
    r'|sk-admin-\w{40,}'                            # OpenAI admin
    r'|sk-ant-[A-Za-z0-9_-]{40,}'                   # Anthropic
    r'|AIza[0-9A-Za-z_-]{35}'                       # Google
    r'|gsk_[A-Za-z0-9]{40,60}'                      # Groq
    r'|hf_[A-Za-z0-9]{30,50}'                       # HuggingFace
    r'|pplx-[A-Za-z0-9]{40,}'                       # Perplexity
    r'|r8_[A-Za-z0-9]{40,}'                         # Replicate
    r'|xai-[A-Za-z0-9]{40,}'                        # xAI
    r'|eyJ[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'  # JWT/Minimax
    r'|(?<![A-Za-z0-9_-])sk-[A-Za-z0-9]{48,}'       # 通用 sk-
    r'|[A-Za-z0-9+/]{40,}={0,2}'                     # Base64-like (access keys)
    r'|\w{32,48}\.\w{16,32}'                         # Zhipu 格式
)

def classify_key(key, context='', filename=''):
    """精确归类密钥到服务商"""
    k = key
    ctx = (context + filename).lower()

    if k.startswith('sk-proj-') or k.startswith('sk-svcacct-') or k.startswith('sk-admin-'):
        return 'overseas', 'OpenAI', 'critical'
    if k.startswith('sk-ant-'):
        return 'overseas', 'Anthropic', 'critical'
    if re.match(r'AIza[0-9A-Za-z_-]{35}', k):
        return 'overseas', 'Google Gemini', 'high'
    if re.match(r'gsk_[A-Za-z0-9]{40,60}', k):
        return 'overseas', 'Groq', 'high'
    if re.match(r'hf_[A-Za-z0-9]{30,50}', k):
        return 'overseas', 'HuggingFace', 'medium'
    if re.match(r'pplx-[A-Za-z0-9]{40,}', k):
        return 'overseas', 'Perplexity', 'high'
    if re.match(r'r8_[A-Za-z0-9]{40,}', k):
        return 'overseas', 'Replicate', 'medium'
    if re.match(r'xai-[A-Za-z0-9]{40,}', k):
        return 'overseas', 'xAI/Grok', 'high'
    if re.match(r'eyJ[A-Za-z0-9_-]{50,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}', k):
        return 'domestic', 'Minimax', 'medium'
    if re.match(r'\w{32,48}\.\w{16,32}', k) and ('zhipu' in ctx or 'glm' in ctx):
        return 'domestic', '智谱GLM', 'high'

    # sk- 通用 --> 按上下文归类
    if re.match(r'sk-[A-Za-z0-9]{48,}', k):
        for kw, (cat, prov) in [
            ('deepseek', ('domestic','DeepSeek')), ('dashscope', ('domestic','通义千问')),
            ('qwen', ('domestic','通义千问')), ('tongyi', ('domestic','通义千问')),
            ('moonshot', ('domestic','Kimi')), ('kimi', ('domestic','Kimi')),
            ('baichuan', ('domestic','百川')), ('stepfun', ('domestic','阶跃星辰')),
            ('volcengine', ('domestic','火山引擎')), ('ark', ('domestic','火山引擎')),
            ('doubao', ('domestic','火山引擎')), ('hunyuan', ('domestic','混元')),
            ('openai', ('overseas','OpenAI')), ('anthropic', ('overseas','Anthropic')),
            ('groq', ('overseas','Groq')), ('cohere', ('overseas','Cohere')),
            ('mistral', ('overseas','Mistral')), ('together', ('overseas','Together AI')),
            ('zhipu', ('domestic','智谱GLM')), ('glm', ('domestic','智谱GLM')),
            ('minimax', ('domestic','Minimax')),
        ]:
            if kw in ctx: return cat, prov, 'high'
        return 'overseas', 'OpenAI', 'critical'

    # Base64-like / generic
    if re.match(r'[A-Za-z0-9+/]{40,}={0,2}', k):
        if 'aws' in ctx or 'access_key' in ctx:
            return 'overseas', 'AWS', 'critical'
        return 'overseas', 'Generic Token', 'medium'

    return 'overseas', 'Other', 'medium'

CAT_LABEL = {'overseas':'海外AI','domestic':'国内AI','proxy':'中转/代理'}
SEV_COLOR = {'critical':red,'high':yellow,'medium':cyan}

# ═══════ 高熵检测 ═══════
def shannon_entropy(s):
    if not s:return 0
    f=Counter(s);n=len(s)
    return -sum(c/n*math.log2(c/n) for c in f.values())

def detect_high_entropy(content, min_len=32, min_entropy=4.0):
    found=[]
    for m in re.finditer(r'''["'`]?([A-Za-z0-9+/=_-]{'''+str(min_len)+r''',})["'`]?''', content):
        c=m.group(1)
        if c.isdigit() or c.isalpha():continue
        if shannon_entropy(c)>=min_entropy:
            ln=content[:m.start()].count('\n')+1
            found.append((c,ln))
    return found

def mask_key(k):
    if len(k)<=12:return k[:4]+'*'*max(len(k)-4,0)
    return k[:6]+'*'*(len(k)-12)+k[-6:]

def key_hash(k):
    return hashlib.sha256(k.encode()).hexdigest()[:16]

# ═══════ 扫描引擎 ═══════
class Scanner:
    def __init__(self,token=''):
        self.s=requests.Session()
        h={'Accept':'application/vnd.github.v3+json','User-Agent':'AI-Key-Scanner/2.0'}
        if token:h['Authorization']=f'Bearer {token}'
        self.s.headers.update(h)
        self.rpm=30 if token else 10
        self.delay=60/self.rpm+1
        self.seen=set()

    def _get(self,url):
        while True:
            try:r=self.s.get(url,timeout=25)
            except:return None
            if r.status_code==403 and 'rate limit' in r.text.lower():
                wt=max(int(r.headers.get('X-RateLimit-Reset',0))-time.time(),60)+5
                sys.stdout.write(f'\r    {yellow(chr(0x231B))} 限速,等{int(wt)}s...');sys.stdout.flush()
                time.sleep(wt);continue
            return r

    def search(self,q):
        url=f'https://api.github.com/search/code?q={quote(q,safe=":")}&per_page=100&sort=indexed'
        r=self._get(url)
        if not r or r.status_code!=200:return[]
        return r.json().get('items',[])

    def download(self,repo,path):
        for br in('main','master'):
            try:
                r=self.s.get(f'https://raw.githubusercontent.com/{repo}/{br}/{path}',timeout=10)
                if r.status_code==200:return r.text
            except:continue
        return None

    def extract(self,content,filename=''):
        keys=[]
        for m in KEY_REGEX.finditer(content):
            key=m.group(0)
            ln=content[:m.start()].count('\n')+1
            sp=content.split('\n')
            ctx=sp[ln-1].strip()[:150] if 0<ln<=len(sp) else ''
            cat,prov,sev=classify_key(key,ctx,filename)
            keys.append({'key':key,'cat':cat,'provider':prov,'severity':sev,'line':ln,'context':ctx})
        return keys

    def run(self,queries,entropy=False):
        print(f'\n  {bold("Queries")}:{len(queries)} | {bold("RPM")}:{self.rpm} | '
              f'{bold("Entropy")}:{green("ON") if entropy else dim("OFF")}')
        print(f'  {dim(chr(0x2500)*60)}\n')
        all_keys=[];tf=0
        for qi,q in enumerate(queries):
            items=self.search(q);nf=0;qkeys=0
            print(f'  {cyan(chr(0x25B6))} [{qi+1:2d}/{len(queries)}] {bold(q[:62])}')
            for it in items:
                repo=it['repository']['full_name'];path=it['path']
                fid=f'{repo}/{path}'
                if fid in self.seen:continue
                self.seen.add(fid);nf+=1;tf+=1
                stars=it['repository'].get('stargazers_count',0)
                lang=it['repository'].get('language','?')
                print(f'     {dim(chr(0x2514))} {dim(repo)}/{dim(path)}  {yellow(chr(0x2B50)+str(stars)) if stars>10 else dim(chr(0x2B50)+str(stars))}  {dim(lang)}',end=' ')
                content=self.download(repo,path)
                if not content:
                    print(f'{red(chr(0x2717))}')
                    continue
                fkeys=0
                for ek in self.extract(content,path):
                    sev_sym=SEV_COLOR.get(ek['severity'],dim)('*')
                    all_keys.append({'repo':repo,'file':path,'line':ek['line'],'key':ek['key'],
                        'cat':ek['cat'],'provider':ek['provider'],'severity':ek['severity'],
                        'context':ek['context'],'stars':stars,'repo_url':it['repository']['html_url'],
                        'repo_lang':lang,'source':'regex'})
                    fkeys+=1;qkeys+=1
                if entropy:
                    for estr,ln in detect_high_entropy(content):
                        all_keys.append({'repo':repo,'file':path,'line':ln,'key':estr,
                            'cat':'overseas','provider':'HighEntropy','severity':'medium',
                            'context':'','stars':stars,'repo_url':it['repository']['html_url'],
                            'repo_lang':lang,'source':'entropy'})
                        fkeys+=1;qkeys+=1
                if fkeys:
                    print(f'{green(chr(0x2713))} {bold(str(fkeys))} keys')
                else:
                    print(f'{dim(chr(0x2713))}')
            print(f'  {dim(chr(0x2514))} {bold(f"files:{nf}")}  keys:{bold(str(qkeys))}  total_files:{tf}  total_keys:{bold(str(len(all_keys)))}')
            if qi<len(queries)-1:
                sys.stdout.write(f'  {dim(f"wait {self.delay:.0f}s...")}')
                sys.stdout.flush()
                time.sleep(self.delay)
                sys.stdout.write('\r'+' '*30+'\r')
                sys.stdout.flush()
        print()
        seen_u=set();dedup=[]
        for k in all_keys:
            uid=f'{k["repo"]}{k["file"]}{k["line"]}{key_hash(k["key"])}'
            if uid not in seen_u:seen_u.add(uid);dedup.append(k)
        return all_keys,dedup

# ═══════ 报告引擎 ═══════
class Report:
    def __init__(self,all_keys,dedup,out):
        self.all=all_keys;self.dedup=dedup;self.out=out
        os.makedirs(out,exist_ok=True)

    def stats(self):
        d=self.dedup;a=self.all
        cats=defaultdict(lambda:{'raw':0,'uniq':0,'repos':set(),'files':set(),'prov':Counter()})
        for k in a:cats[k['cat']]['raw']+=1
        for k in d:
            c=cats[k['cat']];c['uniq']+=1;c['repos'].add(k['repo'])
            c['files'].add(f"{k['repo']}/{k['file']}");c['prov'][k['provider']]+=1
        for c in cats.values():c['repos']=len(c['repos']);c['files']=len(c['files'])
        return cats

    def generate(self):
        ts=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cats=self.stats()
        tr=len(self.all);tu=len(self.dedup)
        trepos=len(set(k['repo'] for k in self.dedup))
        tfiles=len(set(f"{k['repo']}/{k['file']}" for k in self.dedup))

        # TXT
        L=[]
        def h(s):L.append(bold(s))
        def p(s):L.append(s)
        p(chr(0x2550)*66)
        p('  GitHub AI API Key Leak Scan Report')
        p(chr(0x2550)*66)
        p(f'  {ts}')
        p(f'  Raw:{bold(f"{tr:,}")}  Unique:{bold(f"{tu:,}")}  Repos:{bold(f"{trepos:,}")}  Files:{bold(f"{tfiles:,}")}')
        p('')
        for ck in('overseas','domestic','proxy'):
            c=cats[ck]
            if c['uniq']==0:continue
            p(f'  {bold(CAT_LABEL[ck])}: {c["raw"]:,}/{c["uniq"]:,}  repos{c["repos"]:,}  files{c["files"]:,}')
            for prov,cnt in c['prov'].most_common():
                p(f'     {prov:<20s} {cnt:>6,}')
        p('')
        p(chr(0x2500)*66)
        p('  Top 30 (by Stars)')
        p(chr(0x2500)*66)
        for i,k in enumerate(sorted(self.dedup,key=lambda x:-x['stars'])[:30],1):
            sev_sym=SEV_COLOR.get(k.get('severity','medium'),dim)
            stars_str = dim(chr(0x2B50) + str(k['stars']))
            p(f'  [{i:2d}] {sev_sym("*")} {bold(k["repo"])}  {stars_str}')
            p(f'       {dim(k["file"])}:{k["line"]}  [{k["provider"]}]  {dim(k.get("source","?"))}')
            p(f'       {mask_key(k["key"])}')
            if k.get('context'):p(f'       {dim(k["context"][:100])}')
            p('')
        langs=Counter(k.get('repo_lang','?') for k in self.dedup)
        p(chr(0x2500)*66)
        p('  Languages')
        p(chr(0x2500)*66)
        for lang,cnt in langs.most_common(10):p(f'  {lang:<18s} {cnt:>6,}')
        report='\n'.join(L)
        with open(os.path.join(self.out,'scan_summary.txt'),'w',encoding='utf-8')as f:
            f.write(re.sub(r'\033\[\d+m','',report))

        # MD
        md=[]
        md.append('# GitHub AI API Key Leak Scan Report\n')
        md.append(f'> {ts}\n')
        md.append('## Core Data\n')
        md.append('| Metric | Value |');md.append('|--------|-------|')
        md.append(f'| Raw | {tr:,} |');md.append(f'| Unique | {tu:,} |')
        md.append(f'| Repos | {trepos:,} |');md.append(f'| Files | {tfiles:,} |')
        md.append('')
        md.append('## By Category\n')
        md.append('| Category | Raw | Unique | Repos | Files |');md.append('|----------|-----|--------|-------|-------|')
        for ck in('overseas','domestic'):
            c=cats[ck]
            if c['uniq']==0:continue
            md.append(f'| {CAT_LABEL[ck]} | {c["raw"]:,} | {c["uniq"]:,} | {c["repos"]:,} | {c["files"]:,} |')
        md.append('')
        md.append('## By Provider\n')
        for ck in('overseas','domestic'):
            md.append(f'### {CAT_LABEL[ck]}\n')
            for prov,cnt in cats[ck]['prov'].most_common():
                md.append(f'- {prov}: {cnt:,}')
        md.append('')
        md.append('## Top 20\n')
        for i,k in enumerate(sorted(self.dedup,key=lambda x:-x['stars'])[:20],1):
            md.append(f'{i}. **{k["repo"]}** {chr(0x2B50)}{k["stars"]:,}')
            md.append(f'   `{k["file"]}:{k["line"]}` [{k["provider"]}] `{mask_key(k["key"])}`')
            md.append('')
        with open(os.path.join(self.out,'report.md'),'w',encoding='utf-8')as f:
            f.write('\n'.join(md))

        # JSON
        json_out={
            'time':ts,'raw':tr,'unique':tu,'repos':trepos,'files':tfiles,
            'categories':{ck:{'label':CAT_LABEL[ck],'raw':c['raw'],'unique':c['uniq'],
                'repos':c['repos'],'files':c['files'],
                'providers':dict(c['prov'].most_common())} for ck,c in cats.items() if c['uniq']>0},
            'top100':[{'repo':k['repo'],'file':k['file'],'line':k['line'],
                'provider':k['provider'],'severity':k['severity'],
                'key_masked':mask_key(k['key']),'key_hash':key_hash(k['key']),
                'stars':k['stars'],'language':k.get('repo_lang','?'),
                'source':k.get('source','?'),'context':k.get('context','')}
                for k in sorted(self.dedup,key=lambda x:-x['stars'])[:100]],
        }
        with open(os.path.join(self.out,'scan_result.json'),'w',encoding='utf-8')as f:
            json.dump(json_out,f,ensure_ascii=False,indent=2)

        return os.path.join(self.out,'scan_summary.txt'),os.path.join(self.out,'report.md'),os.path.join(self.out,'scan_result.json')


# ═══════ CLI ═══════
def main():
    autoplay_startup_gif()

    BANNER = [
        r'????????????????????????????????????????????????????????????????',
        r'?  r5hhhh2ssi;;iiiiiiiiii;r2hMMMMMMMMMMMMMhhhh5r;ii;;;;;    ?',
        r'?  A233hhhh3Arrrrsiiiiiii2hMMMMhhMMMMMMMMMhhhhMMA;;;;;;;    ?',
        r'?  A25555333552AXAsiiiir3MMhMMhhMMMMhhMMMMMMMMhhM5ii;;;     ?',
        r'?  A22255555352AXXriiirhMhMMhhhMMMMMMhhMMhMMMMMMhM2iiii     ?',
        r'?  ssssXsirsrrrrrrrrrsM3hMM3h3MhMMhMMM3hMh3MMMhhMMMhri      ?',
        r'?  irrrrrrrrrrrrrrrriXh3MMhhh5M2hhh3MM53h53hMMhhhMMMXr      ?',
        r'?  rrrrrrrrrrrrrrrrrrshhMH33h3hA52M5hH22hA33hhhhhhMM3h      ?',
        r'?  rrrrrrrrrrrrrrrrrrA33HM253h53AXA32MAX223555Mhh3M3MS      ?',
        r'?  rrrrrrrrrrrrrrrrrr3X3h33SSH3iH#9GhAhS9h;MHGM33hH3MM      ?',
        r'?  rrrrrrrrrrrsssAAssssrr2hM3hG#99#9#H9####9SMh33523MG      ?',
        r'?  srrsXXXXsXA553MhMHHHH2XAAAX2MS9###S##9#G5XsXsA5HSG       ?',
        r'?  s222hG##MHSSSSSSGSSSGH2MAsAAX3S999999#G2XX2sAMHHHG       ?',
        r'?  5HGGGS#9#SS##SS#####SSGGG5AMAs3MH##SHGG35Hh3MMMHHH       ?',
        r'?  MHGSSS999##99#SSSSS#SGSSSSHMhh3M353HS9GH#9S#GhhMMH       ?',
        r'?  GGSSSS##9####SSSSSSSSGGGGGGHHMh#SGS999SHSS###GMMHH       ?',
        r'?  GGGGGGGGGGGGGGSSSSSSSSSSGGHGHM#9999#999GHSSGGSGGGH       ?',
        r'?  HHHMHHHGGGGGGGGGHHHHMMMMS#99GMG#9999#SS9B&B9SHMhMM       ?',
        r'?  hhhhhhhhhhhhhhh333hhHG3H9&&B&&#SG#9SS9B&&&&&GH9Gh3       ?',
        r'?  GitHub AI Credential Leak Scanner v2                     ?',
        r'????????????????????????????????????????????????????????????????',
    ]
    for line in BANNER:
        print(dim(line))

    p = argparse.ArgumentParser(description='GitHub AI Credential Leak Scanner v2')
    p.add_argument('--token', '-t', default='', help='GitHub PAT (optional)')
    p.add_argument('--deep', '-d', action='store_true', help='Deep scan (46 queries)')
    p.add_argument('--entropy', '-e', action='store_true', help='High-entropy detection')
    p.add_argument('--output', '-o', default=None, help='Output dir')
    args = p.parse_args()

    token = args.token.strip() or os.environ.get('GITHUB_TOKEN', '')
    deep = args.deep
    entropy = args.entropy
    out_dir = args.output or OUTPUT_DIR

    if not token and not deep and not entropy and not args.token and not os.environ.get('GITHUB_TOKEN'):
        print(f'\n  {bold(">>> Interactive Mode <<<")}\n')
        choice = input('  Use GitHub Token? (y/n) [n]: ').strip().lower()
        if choice == 'y':
            token = input('  Paste your GitHub Token: ').strip()
            if not token:
                print(f'  {red("No token entered, running without token.")}')
        elif choice not in ('', 'n'):
            print(f'  {yellow("Invalid choice, running without token.")}')

        print(f'\n  {bold("Select scan mode:")}')
        print(f'    {cyan("[1]")} Fast         (12 queries, ~2 min)')
        print(f'    {cyan("[2]")} Deep         (46 queries, ~8 min)')
        print(f'    {cyan("[3]")} Fast+Entropy (12 queries + entropy)')
        print(f'    {cyan("[4]")} Deep+Entropy (46 queries + entropy)')
        mode = input('  Choice [2]: ').strip() or '2'
        if mode == '1':
            deep, entropy = False, False
        elif mode == '2':
            deep, entropy = True, False
        elif mode == '3':
            deep, entropy = False, True
        elif mode == '4':
            deep, entropy = True, True
        else:
            deep, entropy = True, False

    queries = SEARCH_DEEP if deep else SEARCH_FAST

    print(f'\n  {bold("GitHub AI Credential Leak Scanner v2")}')
    print(f'  {"Token" if token else "No-Token"} | {len(queries)} queries | {"entropy" if entropy else "no-entropy"}')
    print(f'  {dim(f"Output: {out_dir}")}')

    scanner = Scanner(token)
    all_keys, dedup = scanner.run(queries, entropy=entropy)

    if all_keys:
        r = Report(all_keys, dedup, out_dir)
        txt, md, js = r.generate()
        print(f'\n  {green(chr(0x2713))} TXT : {txt}')
        print(f'  {green(chr(0x2713))} MD  : {md}')
        print(f'  {green(chr(0x2713))} JSON: {js}')
    else:
        print(f'\n  {yellow(chr(0x26A0))} No keys found.')
        print('    1. Rate limited -> wait or use token')
        print('    2. Invalid token -> https://github.com/settings/tokens (classic)')

if __name__ == '__main__':
    main()

