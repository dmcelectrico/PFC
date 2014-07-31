#!/usr/bin/python
# -*- coding: utf-8 -*-
import wx
import threading
from wx.lib import masked
from classes import Simulator
import matplotlib.lines as lines

class AcquisitionGUI(wx.Panel):
	def __init__(self, parent,channel_id):
		super(AcquisitionGUI,self).__init__(parent)
		self.parent=parent
		self.InitUI(parent)
		self.drawedPoints = 0
		self.Module = False
		self.channel_id = channel_id

	def InitUI(self,parent):
		self.InitStatusLights()
		# Sizers
		hbox = wx.BoxSizer(wx.HORIZONTAL)	# horizonal layout
		vbox1 = wx.BoxSizer(wx.VERTICAL) 	#first column
		vbox2 = wx.BoxSizer(wx.VERTICAL) 	#second column

		# First column
		#	First row
		hbox1 = wx.BoxSizer(wx.HORIZONTAL) 
		hbox1.Add(wx.StaticText(self, label='Estado: '),flag=wx.ALIGN_LEFT)
		self.statusText= wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_CENTRE)
		self.statusText.SetValue("NO INPUT.")
		hbox1.Add(self.statusText,flag=wx.ALIGN_CENTER)
		self.statusPNG = self.greyLight
		self.imageCtrl = wx.StaticBitmap(self, wx.ID_ANY, wx.BitmapFromImage(self.statusPNG))
		hbox1.Add(self.imageCtrl,border=10,flag=wx.ALIGN_RIGHT)
		vbox1.Add(hbox1, flag=wx.ALIGN_CENTER)

		vbox1.Add(wx.StaticText(self, label='Frecuencia de muestreo:'),flag=wx.ALIGN_CENTER|wx.TOP,border=10)

		#	Sampling rate row
		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		self.samplingRateTCtrl = masked.NumCtrl(self, value=1, fractionWidth=0, allowNegative=False, min=0, max=10000)
		self.samplingRateTCtrl.Bind(wx.EVT_TEXT, self.SamplingRateTextCtrl)
		self.SRMeasure = wx.ComboBox(self, choices=["Hz"],style=wx.CB_READONLY)
		self.SRMeasure.SetSelection(0) 
		self.SRMeasure.Bind(wx.EVT_COMBOBOX, self.SamplingRateComboBox)
		hbox2.Add(self.samplingRateTCtrl,flag=wx.ALIGN_CENTER)
		hbox2.Add(self.SRMeasure,flag=wx.ALIGN_CENTER)
		vbox1.Add(hbox2,flag=wx.ALIGN_CENTER)

		#	Control buttons
		hbox3 = wx.BoxSizer(wx.HORIZONTAL)
		self.pauseButton=wx.Button(self,label="Pausar")
		self.startButton=wx.Button(self,label="Empezar")
		self.pauseButton.Bind(wx.EVT_BUTTON,self.StopClick)
		self.startButton.Bind(wx.EVT_BUTTON,self.StartClick)
		hbox3.Add(self.pauseButton,flag=wx.EXPAND|wx.ALL,border=10)
		hbox3.Add(self.startButton,flag=wx.EXPAND|wx.ALL,border=10)
		vbox1.Add(hbox3,flag=wx.ALIGN_CENTER)

		#	Simulation button
		self.simButton=wx.Button(self,label="Simulación")
		self.simButton.Bind(wx.EVT_BUTTON, self.SimulationClick)
		vbox1.Add(self.simButton,flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=25)

		# Second Column

		self.listCtrl = wx.ListCtrl(self,style=wx.LC_REPORT)
		self.listCtrl.InsertColumn(0,"T (s)")
		self.listCtrl.InsertColumn(1,"Valor")


		# Main sizers arrangements

		hbox.Add(vbox1,1,flag=wx.ALIGN_CENTER|wx.EXPAND)
		hbox.Add(self.listCtrl,3, flag=wx.EXPAND)
		self.SetSizerAndFit(hbox)
		
	"""
		Initializes all the posible light colors.
	"""
	def InitStatusLights(self):
		self.redLight = wx.Image("./graphics/red_light.png",wx.BITMAP_TYPE_PNG).Scale(16,16)
		self.greenLight = wx.Image("./graphics/green_light.png",wx.BITMAP_TYPE_PNG).Scale(16,16)
		self.yellowLight = wx.Image("./graphics/yellow_light.png",wx.BITMAP_TYPE_PNG).Scale(16,16)
		self.greyLight = wx.Image("./graphics/grey_light.png",wx.BITMAP_TYPE_PNG).Scale(16,16)

	""" 
		Changes status light for the panel and returns old bitmap.
	"""
	def SetStatusLight(self,inp):
		old = self.imageCtrl.GetBitmap()
		# if type is wx.Bitmap we show it rightaway
		if type(inp) is wx.Bitmap:
			self.imageCtrl.SetBitmap(inp)
			return old
		#if is a string with the desired color, we need to convert and use the
		#	initialized lights.
		if inp=="red":
			self.imageCtrl.SetBitmap(wx.BitmapFromImage(self.redLight))
		elif inp=="green":
			self.imageCtrl.SetBitmap(wx.BitmapFromImage(self.greenLight))
		elif inp=="yellow":
			self.imageCtrl.SetBitmap(wx.BitmapFromImage(self.yellowLight))
		else:
			self.imageCtrl.SetBitmap(wx.BitmapFromImage(self.greyLight))
		return old

	"""
		Changes status text for the panel and returns old text.
	"""
	def SetStatusText(self,text):
				old = self.statusText.GetValue()
				self.statusText.ChangeValue(text)
				return old

	"""
		Disables widgets so the user won't mess up anything clicking when he's not supposed to.
		TODO
	"""
	def ToggleWidgets(self,status):
		if status==False:
			self.samplingRateTCtrl.Disable()
			self.SRMeasure.Disable()
			self.startButton.Disable()
			self.pauseButton.Disable()
			self.simButton.Disable()
		else:
			self.samplingRateTCtrl.Enable()
			self.SRMeasure.Enable()
			self.startButton.Enable()
			self.pauseButton.Enable()
			self.simButton.Enable()
	
	"""
		Writes the lines read by the Module into the Axes in MainFrame
	"""
	def PushData(self):
		try:
			with self.Module.LOCK:
				x = self.Module.data.x
				y = self.Module.data.y
				self.parent.axes1.add_line(lines.Line2D(x[self.drawedPoints-1:],y[self.drawedPoints-1:]))
				self.drawedPoints=len(x)
		except RuntimeError as inst:
			print type(inst)     # the exception instance
			print inst.args      # arguments stored in .args
			print inst           # __str__ allows args to printed directly
			print len(self.Module.data.x)
			print len(self.Module.data.y)


	#							#
	#	E	V	E	N	T	S	#
	#							#

	def SimulationClick(self,event):
		oldLight = self.SetStatusLight("yellow")
		oldText = self.SetStatusText("Busy...")
		self.ToggleWidgets(False)
		openFileDialog = wx.FileDialog(self, "Abrir fichero CSV", "", "","CSV (*.csv)|*.csv", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		if openFileDialog.ShowModal() == wx.ID_CANCEL:
			self.SetStatusLight(oldLight)
			self.SetStatusText(oldText)
			self.ToggleWidgets(True)
			return     # the user changed idea...

		# proceed loading the file chosen by the user
		# this can be done with e.g. wxPython input streams:
		self.Module = Simulator.Simulator(self.samplingRateTCtrl.GetValue())
		self.Module.setFileInput(openFileDialog.GetPath())
		self.SetStatusLight("red")
		self.SetStatusText("Ready.")
		event.GetEventObject().SetLabel(openFileDialog.GetFilename())
		self.ToggleWidgets(True)

	def StartClick(self,event):
		self.startButton.Disable()
		self.Module.start()
		self.parent.channel_active[self.channel_id]=True
		self.parent.ToggleGraphRefreshing()
		

	def StopClick(self,event):
		self.Module.stop()
		self.startButton.Enable()
		self.parent.channel_active[self.channel_id]=False
		self.parent.ToggleGraphRefreshing()

	def SamplingRateTextCtrl(self,event):
		if self.Module:
			self.Module.sampling_rate = int(self.samplingRateTCtrl.GetValue())
		

	def SamplingRateComboBox(self,event):
		pass




