from snack import *
screen = SnackScreen()
g = Grid(1, 1)
s = Scale(40, 1000)
s.set(0)
g.setField(s, 0, 0)
screen.gridWrappedWindow(g, "Scale Example")
f = Form()
f.add(s) 
for i in range(1000):
	for j in range(10000):
		pass
                s.set(i)
		f.draw()
		screen.refresh()
screen.finish() 
