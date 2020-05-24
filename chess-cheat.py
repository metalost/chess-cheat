#!/usr/bin/env python

DELAY = 100

from pyscreenshot import grab
from stockfish import Stockfish
import tkinter as tk
from board import ChessboardPredictor
from timeout_decorator import timeout, TimeoutError
from multiprocessing import cpu_count

def reorder_rect(x1, y1, x2, y2):
	nx1 = min(x1, x2)
	ny1 = min(y1, y2)
	nx2 = max(x1, x2)
	ny2 = max(y1, y2)
	return nx1, ny1, nx2, ny2

def arrow(r, a, move, corners, active):
	dx = (corners[2] - corners[0]) // 8
	dy = (corners[3] - corners[1]) // 8
	corners[0] += r.bx1
	corners[1] += r.by1
	corners[2] += r.bx1
	corners[3] += r.by1
	move = [ord(move[0])-97, int(move[1])-1, ord(move[2])-97, int(move[3])-1]
	if active == 'b':
		move = [7 - v for v in move]
	move[1] = 7 - move[1]
	move[3] = 7 - move[3]
	move = [int(corners[0] + v*dx + dx/2) if i % 2 == 0 else int(corners[1] + v*dy + dy/2) for i, v in enumerate(move)]
	x1 = min(move[0], move[2])
	y1 = min(move[1], move[3])
	x2 = max(move[0], move[2])
	y2 = max(move[1], move[3])
	x = False
	y = False
	if x1 == x2:
		x1 -= dx // 5
		x2 += dx // 5
		x = True
	if y1 == y2:
		y1 -= dy // 5
		y2 += dy // 5
		y = False
	a.c.delete('all')
	a.c.create_line(move[0]-x1, move[1]-y1, move[2]-x1, move[3]-y1, arrow=tk.LAST, width=10)
	print(move)
	print(move[0]-x1, move[1]-y1, move[2]-x1, move[3]-y1)
	print(x1, y1, x2, y2)
	a.geometry('{}x{}+{}+{}'.format(x2 - x1, y2 - y1, x1, y1))

def init_arrow(r):
	a = tk.Toplevel(r)
	a.overrideredirect(True)
	a.wait_visibility(a)
	a.attributes('-alpha', 0.6)
	a.geometry('0x0')

	c = tk.Canvas(a)
	c.pack(fill=tk.BOTH, expand=True)
	a.c = c
	return a

def init_draw(r):
	d = tk.Toplevel(r)
	d.wait_visibility(d)
	d.attributes('-fullscreen', True)
	d.attributes('-alpha', 0.3)

	c = tk.Canvas(d)
	r.bx1, r.by1, r.bx2, r.by2 = 0, 0, 0, 0
	d.bx1, d.by1, d.bx2, d.by2 = 0, 0, 0, 0

	def save_boundaries():
		r.bx1, r.by1, r.bx2, r.by2 = reorder_rect(d.bx1, d.by1, d.bx2, d.by2)

	def down(e):
		d.bx1, d.by1 = e.x, e.y
		save_boundaries()
		c.delete('all')
	def move(e):
		d.bx2, d.by2 = e.x, e.y
		save_boundaries()
		c.delete('all')
		c.create_rectangle(r.bx1, r.by1, r.bx2, r.by2, width=10)
	def up(e):
		d.bx2, d.by2 = e.x, e.y
		save_boundaries()
		c.delete('all')
		c.create_rectangle(r.bx1, r.by1, r.bx2, r.by2, width=10)
		d.withdraw()
		r.paused = False

	c.bind('<Button-1>', down)
	c.bind('<B1-Motion>', move)
	c.bind('<ButtonRelease-1>', up)

	c.pack(fill=tk.BOTH, expand=True)
	d.withdraw()
	return d

def init_window():
	r = tk.Tk()
	r.title('Chess Cheat')
	r.minsize(190, 20)
	r.attributes('-topmost', True)
	r.paused = False
	r.screenwidth = r.winfo_screenwidth()
	r.screenheight = r.winfo_screenheight()

	v = tk.StringVar()
	white = tk.Radiobutton(r, text='White', variable=v, value='w', indicatoron=0)
	black = tk.Radiobutton(r, text='Black', variable=v, value='b', indicatoron=0)
	white.select()

	l = tk.Label(r, text='')

	d = init_draw(r)

	def draw():
		r.paused = True
		d.deiconify()
	od = tk.Button(r, text='Board', command=draw)

	white.pack()
	black.pack()
	od.pack()
	l.pack()

	a = init_arrow(r)

	return r, v, l, a

def screenshot(r, a):
	img = None
	a.withdraw()
	if (r.bx1 or r.by1 or r.bx2 or r.by2) and r.bx1 != r.bx2 and r.by1 != r.by2:
		img = grab(bbox=(r.bx1, r.by1, r.bx2, r.by2))
	else:
		img = grab()
	a.deiconify()
	return img

@timeout(1, use_signals=False)
def run_stockfish(s, fen):
	s.set_fen_position(fen)
	return s.get_best_move()

def cheat(r, v, l, a, s, b):
	if not r.paused:
		fen, corners = b.fen(screenshot(r, a), v.get())

		#print('Corners: {}'.format(corners))
		#print('FEN: {}'.format(fen))

		if fen:
			try:
				move = run_stockfish(s, fen)
			except TimeoutError:
				s = create_fish()
				r.configure(background='red')
			else:
				#print('Move: {}'.format(move))
				l.config(text=move)
				r.configure(background='green')
				arrow(r, a, move, corners, v.get())
		else:
			r.configure(background='red')

	r.after(DELAY, cheat, r, v, l, a, s, b)

def create_fish():	
	s = Stockfish()
	#s._set_option('Threads', cpu_count())
	#s._parameters.update({'Threads': cpu_count()})
	#s._set_option('Minimum Thinking Time', 10000)
	#s._parameters.update({'Minimum Thinking Time': 10000})
	return s

def main():
	s = create_fish()
	print(s.get_parameters())
	b = ChessboardPredictor()
	r, v, l, a = init_window()
	r.after(100, cheat, r, v, l, a, s, b)
	r.mainloop()
	b.close()

if __name__ == '__main__':
	main()