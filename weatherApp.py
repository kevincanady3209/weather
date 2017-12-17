#!/usr/bin/env python

import gobject
import gtk
import appindicator
from datetime import datetime
import httplib
import syslog

HOST, PORT = "canady.dyndns.org", 8000 
##HOST, PORT = "192.168.0.200", 44444 
UPDATE_TIME = 300
TIMEOUT_TAG = ""

def get_text(parent, message, default=''):
    d = gtk.MessageDialog(parent,
                          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                          gtk.MESSAGE_QUESTION,
                          gtk.BUTTONS_OK_CANCEL,
                          message)
    entry = gtk.Entry()
    entry.set_text(default)
    entry.show()
    d.vbox.pack_end(entry)
    entry.connect('activate', lambda _: d.response(gtk.RESPONSE_OK))
    d.set_default_response(gtk.RESPONSE_OK)

    r = d.run()
    text = entry.get_text().decode('utf8')
    d.destroy()
    if r == gtk.RESPONSE_OK:
        return text
    else:
        return None

class MyApp:
  def my_timer(self):

    try:
        # Receive data from the server and shut down
        conn = httplib.HTTPConnection(HOST,PORT, timeout=5)
        conn.request("GET", "/")
        resp = conn.getresponse()

##        print resp.status, resp.reason
        data = resp.read()

        self.updateTime = datetime.now()
        self.updateTime = self.updateTime.replace(microsecond=0)

        if resp.status == 200 and resp.reason == "OK":
            self.temp,self.humidity,self.windSpeed,self.windGust,self.windDir,self.rain,self.pressure,self.rainRate = data.split("/")        
        
            self.ind.set_label("%s/%s/%smph/%smph/%s/%sin" % (self.temp, self.humidity, self.windSpeed, self.windGust, self.windDir, self.rain))
        else:
            self.ind.set_label("Invalid Server Data.")
        
        conn.close()
    except:
        self.ind.set_label("Failed to connect to Server.")
        
    return True

  def quit(self, widget, data=None):
    gtk.main_quit()

  def detailClose(self, widget, data=None):
    pass
#    print "detailClose\n"

  def showDetails(self, widget, data=None):
#    print "In showDetails\n"

    popup = gtk.Window()
    popup.set_title( "Weather Details" )


    weatherText = "Temperature: " + self.temp + "\n"
    weatherText += "Humidity: " + self.humidity + "\n"
    weatherText += "Wind Speed: " + self.windSpeed + "\n"
    weatherText += "Wind Direction: " + self.windDir + "\n"
    weatherText += "Wind Gust: " + self.windGust + "\n"
    weatherText += "Barometric Pressure: " + self.pressure + "\n"
    weatherText += "Rain: " + self.rain + "\n"
    weatherText += "Rain Rate: " + self.rainRate + "\n" + "\n"

    weatherText += "Last Update: " + str(self.updateTime)

    popup.add( gtk.Label( weatherText ) )
    
    popup.set_modal( True )
    popup.set_transient_for( None )
    popup.set_type_hint( gtk.gdk.WINDOW_TYPE_HINT_DIALOG )
    
    popup.connect( "destroy", self.detailClose )
    
    popup.show_all()

  def getHost(self, widget, data=None):
    global HOST
    ret = get_text(None, "Enter Host", HOST)
    if None != ret:
      HOST = ret
      syslog.syslog('Weather App Updated. Using %s:%d' % (HOST, PORT))
      
  def getPort(self, widget, data=None):
    global PORT
    ret = get_text(None, "Enter Port", str(PORT))
    if None != ret:
      PORT = int(ret)
      syslog.syslog('Weather App Updated. Using %s:%d' % (HOST, PORT))
      
  def getUpdateTime(self, widget, data=None):
    global UPDATE_TIME
    global TIMEOUT_TAG
    
    ret = get_text(None, "Enter Refresh Interval in seconds", str(UPDATE_TIME))
    if None != ret:
      UPDATE_TIME = int(ret)
      gobject.source_remove(TIMEOUT_TAG)
      TIMEOUT_TAG = gobject.timeout_add(UPDATE_TIME * 1000, self.my_timer)
      syslog.syslog('Weather App Updated. Refresh Interval: %d' % UPDATE_TIME)

  def refresh(self, widget, data=None):
      self.my_timer()
      
  def about(self, widget, data=None):
      aboutdialog = gtk.AboutDialog()
      
      aboutdialog.set_name("Kevin's Weather Widget")
      aboutdialog.set_version("1.1")
      aboutdialog.set_copyright("(c) 2012, Kevin Canady")
      aboutdialog.set_authors(["Kevin Canady"])
      aboutdialog.set_comments("Displays weather data from my private weather server.")
      aboutdialog.set_website("http://www.wunderground.com/weatherstation/WXDailyHistory.asp?ID=KTXGARLA15")
      
      aboutdialog.run()
      
      aboutdialog.destroy()
      
  def __init__(self):

    global TIMEOUT_TAG
    
    self.degree = unichr(176)

    self.ind = appindicator.Indicator ("example-simple-client",
                                "weather-clear",
                                appindicator.CATEGORY_APPLICATION_STATUS)
    
    self.ind.set_status (appindicator.STATUS_ACTIVE)
    self.ind.set_attention_icon ("indicator-messages-new")
    
    # create a menu
    self.menu = gtk.Menu()
    

    self.menuName = "Details"
    self.menu_items = gtk.MenuItem(self.menuName)
    self.menu.append(self.menu_items)
    self.menu_items.connect("activate", self.showDetails, self.menuName)
    self.menu_items.show()

    self.hostName = "Host"
    self.host_items = gtk.MenuItem(self.hostName)
    self.menu.append(self.host_items)
    self.host_items.connect("activate", self.getHost, self.hostName)
    self.host_items.show()

    self.portName = "Port"
    self.port_items = gtk.MenuItem(self.portName)
    self.menu.append(self.port_items)
    self.port_items.connect("activate", self.getPort, self.portName)
    self.port_items.show()

    self.updateTimeName = "Refresh Interval"
    self.updateTime_items = gtk.MenuItem(self.updateTimeName)
    self.menu.append(self.updateTime_items)
    self.updateTime_items.connect("activate", self.getUpdateTime, self.updateTimeName)
    self.updateTime_items.show()

    self.refreshName = "Refresh"
    self.refresh_items = gtk.MenuItem(self.refreshName)
    self.menu.append(self.refresh_items)
    self.refresh_items.connect("activate", self.refresh, self.refreshName)
    self.refresh_items.show()

    self.about_item = gtk.MenuItem("About")
    self.about_item.connect("activate", self.about, "status clicked")
    self.about_item.show()
    self.menu.append(self.about_item)

    image = gtk.ImageMenuItem(gtk.STOCK_QUIT)
    image.connect("activate", self.quit)
    image.show()
    self.menu.append(image)
    
    # show the items
    self.ind.set_menu(self.menu)

    self.my_timer()
    TIMEOUT_TAG = gobject.timeout_add(UPDATE_TIME * 1000, self.my_timer)

    
if __name__ == "__main__":

  syslog.syslog('Starting Weather App. Using %s:%d. Refresh Interval: %d' % (HOST, PORT, UPDATE_TIME))
  myApp = MyApp()

  gtk.main()
