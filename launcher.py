#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import curses
import re
from collections import namedtuple
from subprocess import Popen, PIPE


def print_frame(stdscr, max_x):
    '''print window-frame'''

    stdscr.box()
    stdscr.addstr(1, 1, 'Command: z -> zebra, r -> ripd, o -> ospfd, b -> bgpd, k -> UP, j -> DOWN, q -> QUIT', curses.A_NORMAL)
    stdscr.addstr(2, 1, 'Please select the node.', curses.A_NORMAL)
    stdscr.hline(3, 1, curses.ACS_HLINE, max_x - 2)
    stdscr.refresh()      # 画面更新


def end_win(stdscr):
    '''end curses window'''

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()


def launcher(stdscr):
    '''launcher for accessing a quagga daemon'''

    # 移動キーの定義
    c_move = {
        'k':        (lambda x, y: y > swin_size.min_y,
                     lambda x, y: (x, y-1),
                     lambda x, y: (x, y)),
        'KEY_UP':   (lambda x, y: y > swin_size.min_y,
                     lambda x, y: (x, y-1),
                     lambda x, y: (x, y)),
        'j':        (lambda x, y: y < swin_size.max_y,
                     lambda x, y: (x, y+1),
                     lambda x, y: (x, y)),
        'KEY_DOWN': (lambda x, y: y < swin_size.max_y,
                     lambda x, y: (x, y+1),
                     lambda x, y: (x, y)),
        '^U':       (lambda x, y: y >= swin_size.min_y + 10,
                     lambda x, y: (x, y-10),
                     lambda x, y: (x, swin_size.min_y)),
        '^D':       (lambda x, y: y <= swin_size.max_y - 10,
                     lambda x, y: (x, y+10),
                     lambda x, y: (x, swin_size.max_y)),
        '^B':       (lambda x, y: y > swin_size.min_y,
                     lambda x, y: (x, swin_size.min_y),
                     lambda x, y: (x, y)),
        '^F':       (lambda x, y: y < swin_size.max_y,
                     lambda x, y: (x, swin_size.max_y),
                     lambda x, y: (x, y)),
    }

    # デーモン定義
    daemons = {
        'z': 'zebra',
        'r': 'ripd',
        'o': 'ospfd',
        'b': 'bgpd',
    }

    # 画面サイズの取得
    mwin_max_y, mwin_max_x, = stdscr.getmaxyx()

    # サブウィンドウの作成
    swin = stdscr.subwin(mwin_max_y - 2, mwin_max_x - 1, 0, 0)
    swin_size = namedtuple('SubwindowSize',
                           ['min_x', 'max_x', 'min_y', 'max_y'])

    # カーソル移動領域を調整
    swin_size.min_x, swin_size.min_y = 1, 4
    swin_size.max_x = mwin_max_x

    # 現在位置を示すポインタ
    x, y = swin_size.min_x , swin_size.min_y

    # 枠線の描画
    print_frame(stdscr, mwin_max_x)

    # grepパターン
    node_pattern = re.compile(r'.*bash --norc -is mininet:(.*)')

    while True:
       # プロセス一覧の取得
        cmd = 'ps aux'
        proc = Popen(cmd.split(), stdout=PIPE)
        out, err = proc.communicate()

        row = swin_size.min_y  # 表示テストでの行管理

        # ノードリストの作成
        nodes = {}
        for line in str(out).split('\n'):
            match = node_pattern.match(line)
            if not match:
                continue

            name = match.group(1)
            nodes[name] = line.split()[1]

            stdscr.addstr(row, swin_size.min_x, name)  # 表示テスト
            row += 1

        if not nodes:
            sys.stderr.write('Mininet process not found.')
            sys.exit(-1)

        swin_size.max_y = len(nodes) + 3

        # カーソル位置の移動
        stdscr.move(y, x)

        c = stdscr.getkey()  # 入力受付

        if c == 'KEY_RESIZE':
            stdscr.clear()
            mwin_max_y, mwin_max_x, = stdscr.getmaxyx()
            print_frame(stdscr, mwin_max_x)  # フレームの再描画

        elif c == 'q':
            exit()

        elif c in c_move:
            if c_move[c][0](x, y):
                x, y = c_move[c][1](x, y)

        elif c in daemons:
            # 接続処理
            end_win(stdscr)  # 画面解放

            cmd = 'telnet localhost ' + daemons[c]
            # mininetによるtelnet実行
            os.system('mnexec -a %s %s' % (nodes['R1'], cmd))
            exit()
        else:
            for i in xrange(1, swin_size.max_x - 1):
                stdscr.addstr(2, i, ' ')
            stdscr.addstr(2, 1, 'Invalid key: \'%s\'' % c, curses.A_NORMAL)


def main():
    curses.wrapper(launcher)


if __name__ == '__main__':
    main()
