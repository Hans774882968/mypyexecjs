from myexecjs import JsContext
import json
import subprocess

def main():
    goals = [
        'DG1uMMq1M7OeHhds71HlSMHOoI2tFpWCB4ApP00cVFqptmlFKjFu9RluHo2w3mUw',
        '3oimklW/W/ngYkFCAre5DPS4f/d4s9wsxAx+vxTeWY7Ab9AneJtN7AJr9elx7PLpSpxFUXsd0t0=',
        'sZkeRg+OqU4406ZO5EhpRUqsg9QS9dz4BANdNgmpsFVYJjNWn0k61E3lrj05r5EC',
        'evDiDnPBGwIxe3cjYPXB22oKj049pxLL3RfgIp5P9hT+tOtrsevTx29K9aaBj2Ds',
        'o6vkqk+dSV8jKFxlrQPB6S9GITUH4Fx8Kf4EI49OrTgM6c2ehRvua4osLn6iczH/IDcOr0DuFV9KnEVRex3S3Q==',
        'rR95BGefawHYyhz4VPfk6bkheavfgJcELQbGSxEWhB2Sna9EyCwZXhYyvHpf0X7NW3p0MRuPhYdE3KC6Bu3I5A==',
        'nTinqg2MTz6HPcn5po2mvK2hFB6CtN1VNYo3b7BUgrO7cZU7JmI4KETcoLoG7cjk',
        'SZrUq97bIKMT8A8+5poINKp4LvkMho6D22h7QAQdeaVt7lwUBMrzbKGsn4CWgWISSpxFUXsd0t0=',
        'jM2AMHWEGR7XPzcS9TXbFvWk3egklebrLpy4PGOJ2Dgp6gEMy+K7RC1pQBjov5z5',
        'ZbCyikQGss8IGCV14Utz07yC+ltW38oRRtagvPsNby+W5le06WT0SiAI79ae3rHi',
        '4QkDpTPjrgZdr6Mru2jvaxxik7n7Hs3GqA5xX/nVNMnpMvNi8r7WyLUe5gqPTte0+S7G053mkfc=',
        'LpC7uqNRalkxczZr61omV8D/Czy6GJR/0N56qHW8addmWsnr1LQ0VrtxlTsmYjgoRNygugbtyOQ=',
        'RsRBspJvKRto1876nMhHgh3Z6/9buixxfJZedby46Ydoywsc1boyIK4crMvnVmS2OS/I7URLXdw=',
        'OMHyOG8pDj5TH2yMM3zYJtdXdArhLFhp0ArpmcdGlYm87BsE44L1EOVOWatR++TjSpxFUXsd0t0=',
        '6C03P2Jzlff3i0amcVIMM/TdZLftH7b1xUuVHeeTaFlpMOkB0yHNHBbu7Z8EMDtMUVOJ3gkHn5I=',
        'TtulIkS1gMCQiGTImQtOZbPg/A766KPWnRe4RhZ6YxITyudvx3kTgiR0UGwcAEzr',
        'JWGteWDj2RBfHGC0jr8quHNUoJyrK2yIallL/iGyNwk=',
    ]
    crypto_js = 'crypto.js'
    ctx = JsContext(open(crypto_js,encoding = 'utf-8').read())

    hans = {
        'name': 'hans',
        'image': 'hans.png',
        'birthday': '1995-02-28',
        'height': '183cm',
        'weight': '58.8KG'
    }
    res = ctx.eval(f"getToken({json.dumps(hans,ensure_ascii = False)})")
    print(res,type(res),len(res))

    players = ctx.eval('players')
    players.append(hans)
    want1 = []
    # 效率问题挺严重的
    for p in players:
        want1.append(ctx.eval(f'getToken({json.dumps(p,ensure_ascii = False)})'))
    print(want1)

    want2 = ctx.eval('players.map(p => getToken(p))')
    print(want2)
    want2.append(res)
    assert want1 == goals and want2 == goals

if __name__ == '__main__':
    main()