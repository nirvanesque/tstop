#TSTOP
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


import argparse
import itertools
import functools
import os
import os.path
import sys
import csv
# Used to guarantee to use at least Wx2.8
import wxversion
wxversion.ensureMinimal('2.8')

import matplotlib

matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from matplotlib.figure import Figure

import wx

from persistence.Segment import SegmentFileDescriptor
from persistence import PersistenceGenerator
from persistence import PersistenceKernel
from persistence.py_persistence import ScaleSpaceKernel

usage = "usage: python plot_activity.py data.csv"
colors = ['green','red','blue','orange','purple','yellow','black','grey']

class DataSpan:
    def __init__(self, label):
        self.label = label
        self.data=[]
    def addData(self, new_data):
        self.data.extend([new_data])


class CanvasFrame(wx.Frame):

    def __init__(self, filename, index_column, label_column, window_size, window_stride, max_simplices, kernel_scale):
        wx.Frame.__init__(self,None,-1,
                         'Data Visualization',size=(550,350))
        self.filename = filename
        self.index_column = index_column
        self.label_column = label_column
        self.window_size   = window_size
        self.window_stride = window_stride
        self.max_simplices = max_simplices
        self.kernel_scale = kernel_scale
        
        self.spans = []
        with open(self.filename, 'r') as data_file :
            self.data_len = len(csv.reader(data_file, delimiter=',').next())
        self.data_indices = [ i for i in range(0,self.data_len) \
                              if not ((i == self.index_column) or (i == self.label_column) or \
                                      (((self.index_column == -1) or (self.label_column == -1)) and (i == self.data_len-1)))]
        print "Data indicies %s" % (self.data_indices,)

        with open(self.filename, 'r') as data_file :
            data_reader = csv.reader(data_file, delimiter=',')
            last_label = -1
            for (index, line) in itertools.izip(itertools.count(0), data_reader) :
                if line[self.label_column] != last_label :
                    self.spans.extend([DataSpan(line[self.label_column])])

                self.spans[-1].addData([index] + [line[i] for i in self.data_indices])
                last_label = line[self.label_column]
        print "Spans %s" % (["elements %s label %s" % (len(span.data), span.label) for span in self.spans]) 
        self.labels = set([span.label for span in self.spans])
        
        self.index = 1

        self.SetBackgroundColour(wx.NamedColour("WHITE"))
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)

        self.canvas = FigureCanvas(self, -1, self.figure)
        self.click_cid_down = self.canvas.mpl_connect('button_press_event', self.mouseDown)
        self.click_cid_up = self.canvas.mpl_connect('button_release_event', self.mouseUp)
        self.click_cid_move = self.canvas.mpl_connect('motion_notify_event', self.mouseMove)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(NavigationToolbar2Wx(self.canvas), 1, wx.LEFT | wx.TOP | wx.GROW)
        self.sizer.Add(self.canvas, 8, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.title = self.figure.suptitle("Data for Column %s" % (self.index,))
        self.caption = self.figure.text(0.25, 0.8, "%s Samples Read" % (\
            reduce((lambda x,y: x+y),[len(span.data) for span in self.spans], 0)))
        self.Fit()
        self.background = self.axes.figure.canvas.copy_from_bbox(self.axes.bbox)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_KEY_UP, self.KeyEvent)
        self.point_Refresh()
        self.state = (None, 0)


    def mouseDown(self, event):
        if (event != None and event.xdata != None) :
            click_span = None
            for span in self.spans:
                if span.data[0][0] < event.xdata and span.data[-1][0] > event.xdata :
                    click_span = span
                    break
            if (click_span != None) :
                if self.state[0] == None or self.state[0] != 'mouse up' :
                    self.state = ('mouse down', event.xdata)
                self.caption.set_text("Span Label %s start %s end %s size %s" % (
                    click_span.label, click_span.data[0][0], click_span.data[-1][0], len(click_span.data)))
            else :
                self.caption.set_text("No span at %s, %s" % (event.xdata, event.ydata))
                
            wx.PostEvent(self,wx.PaintEvent())

    def mouseUp(self, event):
        if (event != None and event.xdata != None) :
            click_span = None
            for span in self.spans:
                if span.data[0][0] < event.xdata and span.data[-1][0] > event.xdata :
                    click_span = span
                    break
            if (click_span != None) :
                self.caption.set_text("Span Label %s start %s end %s size %s" % (
                    click_span.label,click_span.data[0][0], click_span.data[-1][0], len(click_span.data)))
                if self.state[0] != None and self.state[0] == 'mouse down' :
                    self.state = ('mouse up', (self.state[1], event.xdata))
                elif self.state[0] != None and self.state[0] == 'mouse up' :
                    start_0 = min(self.state[1][0], self.state[1][1])
                    end_0   = max(self.state[1][0], self.state[1][1])
                    start_1 = event.xdata - (end_0 - start_0) / 2
                    end_1   = event.xdata + (end_0 - start_0) / 2
                    if start_1 < 0 :
                        start_1 = 0
                        end_1   = end_0 - start_0
                    elif end_1 > self.spans[-1].data[-1][0] :
                        end_1 = self.data_len
                        start_1 = end_1 - (end_0 - start_0)

                    sfd = SegmentFileDescriptor.fromSegmentList([dict([('file',           self.filename),
                                                                       ('label index',    self.label_column),
                                                                       ('data index',     self.index),
                                                                       ('segment start',  int(start_0)),
                                                                       ('segment size',   int(end_0 - start_0)),
                                                                       ('segment stride', int(abs(start_1 - start_0))),
                                                                       ('window size',    self.window_size),
                                                                       ('window stride',  self.window_stride)]),
                                                                 dict([('file',           self.filename),
                                                                       ('label index',    self.label_column),
                                                                       ('data index',     self.index),
                                                                       ('segment start',  int(start_1)),
                                                                       ('segment size',   int(end_1 - start_1)),
                                                                       ('segment stride', int(abs(start_1 - end_1))),
                                                                       ('window size',    self.window_size),
                                                                       ('window stride',  self.window_stride)])])
                    pg = PersistenceGenerator.PersistenceGenerator(sfd, max_simplices=self.max_simplices)
                    persistences = map(PersistenceGenerator.process, itertools.product(sfd, [self.max_simplices]))
                    pk = PersistenceKernel.PersistenceKernel(training_list=persistences, 
                                                             testing_list=None,
                                                             degree=1,
                                                             kernel=(lambda a,b: ssk_similarity(a,b,self.kernel_scale)))
                    print "Computed similarity between Segment 0 (%s, %s) and Segment 1 (%s, %s) : %s" % (\
                        int(start_0), int(end_0), int(start_1), int(end_1), pk.compute_training()[0][1],)
                    self.state = (None, 0)

            else :
                self.caption.set_text("No span at %s, %s" % (event.xdata, event.ydata))
                
            wx.PostEvent(self,wx.PaintEvent())

    def mouseMove(self, event):
        if (event != None and event.xdata != None) :
            click_span = None
            for span in self.spans:
                if span.data[0][0] < event.xdata and span.data[-1][0] > event.xdata :
                    click_span = span
                    break
            if (click_span != None) :
                self.caption.set_text("Span Label %s start %s end %s size %s" % (
                    click_span.label,click_span.data[0][0], click_span.data[-1][0], len(click_span.data)))
            else :
                self.caption.set_text("No span at %s, %s" % (event.xdata, event.ydata))
                
            wx.PostEvent(self,wx.PaintEvent())

    def point_Refresh(self) :
        self.canvas.restore_region(self.background)
        self.title.set_text("Activity Data for Column %s" % (self.index,))
        self.axes.cla()
        for span in self.spans :
            xs = [p[0] for p in span.data]
            ys = [p[self.index] for p in span.data]
            self.axes.plot(xs,ys,color=colors[int(span.label)])

    def KeyEvent(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_LEFT :
            self.index = (self.index - 2) % len(self.data_indices) + 1

            self.SetTitle("Column %s" % (self.data_indices[self.index-1],))
            self.point_Refresh()
            wx.PostEvent(self,wx.PaintEvent())
        elif keycode == wx.WXK_RIGHT :
            self.index = (self.index) % len(self.data_indices) + 1
            
            self.SetTitle("Column %s" % (self.data_indices[self.index-1],))
            self.point_Refresh()
            wx.PostEvent(self,wx.PaintEvent())
        else :
            self.point_Refresh()
            wx.PostEvent(self,wx.PaintEvent())
            event.Skip()
            
    def OnPaint(self, event):
        paint_dc = wx.PaintDC(self)
        self.canvas.draw()

class App(wx.App):
    def __init__(self, arg, filename, index_column, label_column, window_size, window_stride, max_simplices, kernel_scale):
        self.filename = filename
        self.index_column = index_column
        self.label_column = label_column
        self.window_size = window_size
        self.window_stride = window_stride
        self.max_simplices = max_simplices
        self.kernel_scale = kernel_scale
        wx.App.__init__(self,0)

    def OnInit(self):
        'Create the main window and insert the custom frame'
        frame = CanvasFrame(self.filename, self.index_column, self.label_column, self.window_size, self.window_stride, self.max_simplices, self.kernel_scale)
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

def main(argv) :
    parser = argparse.ArgumentParser(description='Data Visualization to guesstimate segment sizes')
    parser.add_argument('-f', '--input-file', help="Input CSV file to examine")
    parser.add_argument('-i', '--index-column', default='0', type=int, help="Column in CSV containing the index of the data")
    parser.add_argument('-l', '--label-column', default='-1', type=int, help="Column in CSV containing the data labeling (-1 is the last column)")
    parser.add_argument('-w', '--window-size', default='50', type=int)
    parser.add_argument('-W', '--window-stride', default='1', type=int)
    parser.add_argument('-s', '--max-simplices', default='200000', type=int)
    parser.add_argument('-k', '--kernel-scale', default='0.5', type=float)
    args = vars(parser.parse_args(argv[1:]))
    current_dir = os.getcwd()
    filename       = args['input_file']
    index_column   = args['index_column']
    label_column   = args['label_column']
    window_size    = args['window_size']
    window_stride  = args['window_stride']
    max_simplices  = args['max_simplices']
    kernel_scale   = args['kernel_scale']

    if (filename[0] == '~') :
        filename = os.path.expanduser(filename)
    elif (filename[0] != '/') :
        filename = "%s/%s" % (current_dir, filename)

    try:
        app = App(0, filename, index_column, label_column, window_size, window_stride, max_simplices, kernel_scale)
        app.MainLoop()

    except KeyboardInterrupt:
        print "Caught cntl-c, shutting down..."
        exit(0)
        

if __name__ == "__main__":
        main(sys.argv)
