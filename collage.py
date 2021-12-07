#!/usr/bin/env python3
from PIL import Image, ImageFilter, ImageOps
import sys
import argparse
import random
import math

parser = argparse.ArgumentParser()

parser.add_argument(
  "--width", "-W", type=int, default=1920,
  help="Width in pixels of output image"
)

parser.add_argument(
  "--height", "-H", type=int, default=1080,
  help="Height in pixels of output image"
)

parser.add_argument(
  "--background", "-B", type=str, default="#13254B",
  help="Background color beneath the collage, specify '#00000000' for completely transparent background"
)

parser.add_argument(
  "--border", "-b", type=int, default=100,
  help="""
    Size of offset from edges for the initial repetition grid, creating a border of empty space.
    This is calculated before noise is added to sample placement, so this does not guarantee any border.
    A larger value makes it more likely samples will not be placed outside the image boundary.
  """
)

parser.add_argument(
  "--density", "-d", type=float, default=10,
  help="Repetition density of samples, measured in quantity of samples intersected by the image diagonal."
)

parser.add_argument(
  "--scale", "-s", type=float, default=1.0,
  help="""
    Scale factor for resizing of the repeated items (useful for when -W and -H are very large or small)
  """
)

parser.add_argument(
  "--noise", "-n", type=int, default=50,
  help="Maximum range for randomization of grid placement and resizing of repeated samples in pixels"
)

parser.add_argument(
  "--shadow-size", "-S", type=int, default=10,
  help="Shadow length in pixels around each side of foreground"
)

parser.add_argument('paths', nargs='+')

args = parser.parse_args()


def get_diagonal(w,h):
  return math.sqrt(w**2 + h**2)


def cycle(items):   # there's itertools.cycle but this spells out the generator
  while True:
    yield from items


background = Image.new('RGBA', (args.width, args.height), args.background)

images = []
min_width = 0xffffffff
min_height = 0xffffffff

# Add drop-shadow to each base image so we don't
#    have to add it to each randomized placement
for image_path in args.paths:
  image = Image.open(image_path).convert('RGBA')

  shadow_size2 = args.shadow_size * 2
  shadow_width = image.width+shadow_size2
  shadow_height = image.height+shadow_size2
  shadow_size = (shadow_width,shadow_height)
  shadow_offset = ( (ss_2:=args.shadow_size//2), ss_2 )

  shadow = Image.new('RGBA', shadow_size, (0, 0, 0, 0))
  shadow.paste(Image.new('RGBA', image.size, (0,0,0,255)), shadow_offset, image)
  shadow = shadow.filter(ImageFilter.GaussianBlur(radius=args.shadow_size))
  shadow.paste(image, shadow_offset, image)
  images.append(shadow)

  if min_width  > shadow.width:  min_width  = shadow.width
  if min_height > shadow.height: min_height = shadow.height


min_width  = round(min_width*args.scale)
min_height = round(min_height*args.scale)
min_size   = (min_width, min_height)

for i in images:
  i.thumbnail(min_size)  # thumbnail mutates in place


border = args.border

x_range = (border, args.width  - border )
y_range = (border, args.height - border)


diagonal  = get_diagonal(args.width, args.height)
x_density = round(args.width  * args.density / diagonal) or 1
y_density = round(args.height * args.density / diagonal) or 1
points    = x_density * y_density
x_step    = (x_range[1]-border) // (x_density-1)
y_step    = (y_range[1]-border) // (y_density-1)


image_iter = cycle(images)
i = 0
y = border

for yi in range(y_density):
  x = border
  random.shuffle(images)
  for xi in range(x_density):
    image = image_iter.__next__()


    rotation = random.random()*60 * (-1 if random.random() > 0.5 else 1)
    x_noise  = random.randint(-args.noise, args.noise)
    y_noise  = random.randint(-args.noise, args.noise)


    _image = image.rotate(rotation, expand=True, translate=None, fillcolor=(0,0,0,0))

    if random.choice((True, False)):
      _image = _image.transpose(Image.FLIP_LEFT_RIGHT)

    while True:
      try:
        _scale = (random.random() * args.noise * random.choice((1,-1)))
        _image.thumbnail((min_width+_scale, min_height+_scale), Image.ANTIALIAS)
        break
      except ValueError:
        continue

    _x = x + x_noise - (image.width >> 1)
    _y = y + y_noise - (image.height >> 1)

    background.alpha_composite(_image, dest=(_x,_y))


    i +=1
    print(f"\r{100*i/points:0.2f}% ", end='')

    x += x_step
  y += y_step


background.save('collage.png')
print("done")
