#!/usr/bin/env python3

from PIL import Image, ImageDraw, ImageFont, ImageOps
import math
import sys


# 
def value_to_color ( value, max_val ):
  fraction_of_range = value / max_val
  #print ( "values: ", value, max_val, "fraction of range: ", fraction_of_range )

  # Red ----------------------------------------------
  if fraction_of_range <= 0.10 :
    percents = 100 * fraction_of_range
    red = int(percents * 8.0)   # max 80, 80
  elif fraction_of_range <= 0.20 :
    percents_above_10 = 100 * (fraction_of_range - 0.10)
    red = 80 + int(percents_above_10 * 3.2)   # max 32, 112
  elif fraction_of_range <= 0.30 :
    percents_above_20 = 100 * (fraction_of_range - 0.20)
    red = 112 + int(percents_above_20 * 2.7)  # max 27, 139
  elif fraction_of_range <= 0.40 :
    percents_above_30 = 100 * (fraction_of_range - 0.30)
    red = 139 + int(percents_above_30 * 2.3)   # max 23, 162
  elif fraction_of_range <= 0.50 :
    percents_above_40 = 100 * (fraction_of_range - 0.40)
    red = 162 + int(percents_above_40 * 1.8)   # max 18, 180
  elif fraction_of_range <= 0.60 :
    percents_above_50 = 100 * (fraction_of_range - 0.50)
    red = 180 + int(percents_above_50 * 1.8)   # max 18, 198
  elif fraction_of_range <= 0.70 :
    percents_above_60 = 100 * (fraction_of_range - 0.60)
    red = 198 + int(percents_above_60 * 1.4)   # max 14, 212
  elif fraction_of_range <= 0.80 :
    percents_above_70 = 100 * (fraction_of_range - 0.70)
    red = 212 + int(percents_above_70 * 1.5)   # max 15, 227
  elif fraction_of_range <= 0.90 :
    percents_above_80 = 100 * (fraction_of_range - 0.80)
    red = 227 + int(percents_above_80 * 1.4)   # max 14, 241
  else :
    percents_above_90 = 100 * (fraction_of_range - 0.90)
    red = 180 + int(percents_above_90 * 1.4)   # max 14, 255
    if red > 255 :
      red = 255
  


  # Green ----------------------------------------------
  if fraction_of_range <= 0.20 :
    green = 0
  elif fraction_of_range <= 0.30 :
    percents_above_20 = 100 * (fraction_of_range - 0.20)
    green = int(percents_above_20 * 0.6)   # max 6
  elif fraction_of_range <= 0.40 :
    percents_above_30 = 100 * (fraction_of_range - 0.30)
    green = 6 + int(percents_above_30 * 0.8)  # max 14
  elif fraction_of_range <= 0.50 :
    percents_above_40 = 100 * (fraction_of_range - 0.40)
    green = 14 + int(percents_above_40 * 1.5)   # max 29
  elif fraction_of_range <= 0.60 :
    percents_above_50 = 100 * (fraction_of_range - 0.50)
    green = 29 + int(percents_above_50 * 2.5)   # max 54
  elif fraction_of_range <= 0.70 :
    percents_above_60 = 100 * (fraction_of_range - 0.60)
    green = 54 + int(percents_above_60 * 3.2)   # max 86
  elif fraction_of_range <= 0.80 :
    percents_above_70 = 100 * (fraction_of_range - 0.70)
    green = 86 + int(percents_above_70 * 4.2)   # max 128
  elif fraction_of_range <= 0.90 :
    percents_above_80 = 100 * (fraction_of_range - 0.80)
    green = 128 + int(percents_above_80 * 4.2)   # max 180
  else :
    percents_above_90 = 100 * (fraction_of_range - 0.90)
    green = 180 + int(percents_above_90 * 7.5) 
    if green > 255 :
      green = 255


  # Blue ----------------------------------------------
  if fraction_of_range <= 0.10 :
    percents = 100 * fraction_of_range
    blue = int(percents * 15)   # max 150, 150
  elif fraction_of_range <= 0.20 :
    percents_above_10 = 100 * (fraction_of_range - 0.10)
    blue = 150 + int(percents_above_10 * 9.1)   # max 91, 241
  elif fraction_of_range <= 0.25 :
    percents_above_20 = 100 * (fraction_of_range - 0.20)
    blue = 241 + int(percents_above_20 * 1.4)   # max 14, 255
  elif fraction_of_range <= 0.30 :
    percents_above_25 = 100 * (fraction_of_range - 0.25)
    blue = 255 + int(percents_above_25 * -0.8)  # max 2, 243
  elif fraction_of_range <= 0.40 :
    percents_above_30 = 100 * (fraction_of_range - 0.30)
    delta = int(percents_above_30 * -9.2)
    #print ( "delta: ", delta )
    blue = 243 + delta                          # max -92, 151
  elif fraction_of_range <= 0.50 :
    percents_above_40 = 100 * (fraction_of_range - 0.40)
    delta = int(percents_above_40 * -14.1)
    #print ( "delta: ", delta )
    blue = 151 + delta                          # max -141, 10
  elif fraction_of_range <= 0.60 :
    percents_above_50 = 100 * (fraction_of_range - 0.50)
    blue = 10 + int(percents_above_50 * -1.0)   # max -10, 0
  else :
    blue = 0
  
  if blue > 255:
    blue = 255

  return ( int(red), int(green), int(blue) )




def draw_data ( file_name, data_box_size, grand_max_val ) :
  with open(file_name) as f:
      threeples = [tuple(map(float, line.split(' '))) for line in f]

  #print ( threeples )
  max_x = math.ceil(max(threeples, key=lambda tup: tup[0])[0])
  min_x = math.ceil(min(threeples, key=lambda tup: tup[0])[0])
  max_y = math.ceil(max(threeples, key=lambda tup: tup[1])[1])
  min_y = math.ceil(min(threeples, key=lambda tup: tup[1])[1])

  min_val = min(threeples, key=lambda tup: tup[2])[2]
  #max_val = max(threeples, key=lambda tup: tup[2])[2]

  # Except -- I don't want to use max_val from this data set.
  # I want to use the global max val for all data sets, so I 
  # get it passed in from main.

  #print ( "min_x: ", min_x, " min_y: ", min_y )

  image_width  = (1+max_x-min_x) * data_box_size
  image_height = (1+max_y-min_y) * data_box_size

  rimg = Image.new ( mode="RGB", size=(image_width, image_height) )
  rimg_draw = ImageDraw.Draw ( rimg )

  fontsize = 30
  f = ImageFont.truetype ( font='/usr/share/fonts/liberation-serif/LiberationSerif-Regular.ttf', size=fontsize )

  count = 0
  for threeple in threeples :
    count = count + 1
    x   = threeple[0] 
    y   = threeple[1] 
    val = threeple[2]

    #print ( "--------------------- ", count )
    #print ( "x: ", x, " y: ", y )
    x = x - min_x
    y = 1 + y - min_y
    #print ( "x: ", x, " y: ", y )
    x = x * data_box_size
    y = y * data_box_size
    y = image_height - y
    #print ( "x: ", x, " y: ", y )

    w = data_box_size
    h = data_box_size
    (r, g, b) = value_to_color ( val, grand_max_val )
    #print ( "value: ", val, " colors: ", r, g, b )
    rimg_draw.rectangle((x, y, x+data_box_size, y+data_box_size), fill=(r, g, b), outline=(0, 0, 0))

    if val < 10 :
      label = "{:.2f}".format(val)
    else :
      label = "{:.1f}".format(val)

    y_offset = (data_box_size / 2) - fontsize / 2
    x_offset = 20

    x_pos = x + x_offset
    y_pos = y + y_offset

    if val <= 6 :
      rimg_draw.text((x_pos, y_pos), label, (255, 255, 255), font=f)
    else :
      rimg_draw.text((x_pos, y_pos), label, (0, 0, 0), font=f)

  return rimg



def make_labeled_image ( data_image, 
                         n_streams, 
                         data_box_size,
                         x_label_origin,
                         x_label_size,
                         y_label_origin,
                         y_label_size ) :

  data_image_width, data_image_height = data_image.size

  #print ( data_image_width, data_image_height )
  border_width = 200
  display_image_width  = data_image_width  + 2*border_width
  display_image_height = data_image_height + 2*border_width

  display_image = Image.new ( mode="RGB", size=(display_image_width, display_image_height) )
  display_image_draw = ImageDraw.Draw ( display_image )

  display_image.paste ( data_image, box = ( border_width, border_width ) )

  # Open the fonts ----------------------------------
  number_fontsize = 40
  number_font = ImageFont.truetype ( font='/usr/share/fonts/liberation-serif/LiberationSerif-Regular.ttf', size=number_fontsize )

  label_fontsize = 60
  label_font = ImageFont.truetype ( font='/usr/share/fonts/liberation-serif/LiberationSerif-Regular.ttf', size=label_fontsize )


  # Write the bottom label ----------------------------------
  y_pos = border_width + data_image_height + number_fontsize/4
  for i in range ( x_label_origin, x_label_origin + x_label_size ) :
    x_pos = int(border_width + data_box_size * (i-1) + data_box_size/2)
    label = str(i)
    display_image_draw.text((x_pos, y_pos), label, (255, 255, 255), font=number_font)

  label = "Inter-Router Connections"
  y_pos = y_pos + int( 1.5 * number_fontsize)
  x_pos = border_width + 100
  display_image_draw.text((x_pos, y_pos), label, (255, 255, 255), font=label_font)

  # Write the Y-axis Numbers ----------------------------------
  x_pos = int(border_width/2)
  y_axis_count=0
  for i in range(y_label_origin, y_label_origin + y_label_size) :
    # Position at the next box up, because the origin point of the string 
    # is at the string's *top*.
    y_pos = (border_width + data_image_height) - (y_axis_count+1) * data_box_size + data_box_size/2
    y_axis_count = y_axis_count + 1
    label = str(i)
    display_image_draw.text((x_pos, y_pos), label, (255, 255, 255), font=number_font)

  # The Y-Axis Label --------------------------------------
  text_layer_height = int(90)
  text_layer = Image.new('L', (700, text_layer_height))
  draw = ImageDraw.Draw ( text_layer )
  draw.text( (30, 0), "Worker Threads per Router",  font=label_font, fill=255)
  rotated_text_layer = text_layer.rotate(90.0, expand=1)
  x_pos = int(10)
  y_pos = int(border_width + data_box_size/2)
  display_image.paste( ImageOps.colorize(rotated_text_layer, (0,0,0), (255, 255, 255)), (x_pos, y_pos),  rotated_text_layer)


  # Main Title --------------------------------------
  label = "Throughput in Gbits/sec for " + n_streams + " Input Streams"
  x_pos = 75
  y_pos = int ( border_width / 4 )
  display_image_draw.text((x_pos, y_pos), label, (255, 255, 255), font=label_font)

  return display_image



# Main =================================


file_name      = sys.argv[1]
n_streams      = sys.argv[2]
x_label_origin = int(sys.argv[3])
x_label_size   = int(sys.argv[4])
y_label_origin = int(sys.argv[5])
y_label_size   = int(sys.argv[6])
grand_max_val  = int(sys.argv[7])

data_box_size  = 100

data_image = draw_data ( file_name, data_box_size, grand_max_val )

final_image = make_labeled_image ( data_image, 
                                   n_streams, 
                                   data_box_size,
                                   x_label_origin,
                                   x_label_size,
                                   y_label_origin,
                                   y_label_size )

# Save and Show ----------------------------------
final_image.save ( file_name + ".jpg" )
#final_image.show ( )



