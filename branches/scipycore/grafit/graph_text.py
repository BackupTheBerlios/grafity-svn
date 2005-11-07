import binascii
import os

import numarray.mlab as mlab
import Image
import ImageFont
import ImageDraw
from thirdparty.ft2font import FT2Font

import grafit.thirdparty.mathtextg as mathtext
from grafit.settings import DATADIR
from grafit.arrays import *
from OpenGL.GL import *
import time

from graph_render import *

from __builtin__ import round

FONTFILE = os.path.join(DATADIR, 'data', 'fonts', 'bitstream-vera', 'Vera.ttf')

# You have: points
# You want: mm
#         * 0.3514598
#         / 2.8452756

def cut(st, delim):
    pieces = st.split(delim)
    pieces_fixed = []
    if st == '':
        return []

    pieces_fixed.append(pieces[0])

    for p, q in (pieces[n:n+2] for n in range(len(pieces)-1)):
        if (len(p) - len(p.rstrip('\\'))) % 2:
            # has an odd number of trailing backslashes
            pieces_fixed[-1] += delim+q
        else:
            pieces_fixed.append(q)
    if pieces_fixed[0] == '':
        initial = True
        del pieces_fixed[0]
    else: 
        initial = False

    if pieces_fixed[-1] == '':
        del pieces_fixed[-1]

    return zip(pieces_fixed, [bool(x%2)^initial for x in range(len(pieces_fixed))])


class TextPainter(object):
    def __init__(self, graph):
        self.plot = graph

    #########################################################################
    # Rendering text                                                        #
    #########################################################################

    # Text objects are split into chunks, which are fragments
    # that have the same size and the same type (normal, tex, ...)

    # The render_text_chunk_xxx functions return the size of the
    # text fragment and a renderer. The renderer must be called
    # with the position (lower left corner) of the fragment, 
    # to render the text

    def render_text_chunk_symbol(self, text, size=None, orientation='h'):
        def renderer(x, y):
            try:
                d = self.plot.datasets[int(text)]
            except (ValueError, IndexError):
                print >>sys.stderr, 'error!'
                return 0, 0, 0, None
            xmin, ymin = self.plot.data_to_phys(self.plot.xmin, self.plot.ymin)
            xmax, ymax = self.plot.data_to_phys(self.plot.xmax, self.plot.ymax)
            x, y = self.plot.phys_to_data(x, y)
            glColor4f(d.style.color[0]/256., d.style.color[1]/256., 
                      d.style.color[2]/256., 1.)
            symbols = ['circle', 'square', 'diamond', 'uptriangle',
                       'downtriangle', 'lefttriangle', 'righttriangle']

            render_symbols(array([x]), array([y]),
                           symbols.index(d.style.symbol[:-2]), ['o', 'f'].index(d.style.symbol[-1]),
                           d.style.symbol_size, xmin, xmax, ymin, ymax,
                           self.plot.plot_width, self.plot.plot_height,
                           self.plot.xmin, self.plot.xmax, self.plot.ymin, self.plot.ymax,
                           self.plot.xtype == 'log', self.plot.ytype == 'log')

        return 15, 15, -7.5, renderer

    def render_text_chunk_normal(self, text, size, orientation='h'):
        fonte = ImageFont.FreeTypeFont(FONTFILE, int(round(size)))
        w, h = fonte.getsize(text)
        ascent, descent = fonte.getmetrics()
        origin = h - ascent
        if self.plot.ps:
            origin = 0
        if orientation == 'v': 
            ww, hh, angle = h, w, 90.0
        else: 
            ww, hh, angle = w, h, 0.0

        def renderer(x, y):
            if self.plot.ps:
                glColor4f(0, 0, 0, 1)
                glRasterPos2d(x, y)
                font = FT2Font(str(FONTFILE))
                fontname = font.postscript_name
                gl2ps_TextOpt(text, fontname, size, GL2PS__TEXT_BL, angle)
            else:
                image = Image.new('L', (w, h), 255)
                ImageDraw.Draw(image).text((0, 0), text, font=fonte)
                image = image.transpose(Image.FLIP_TOP_BOTTOM)
                if orientation == 'v':
                    image = image.transpose(Image.ROTATE_270)
                glRasterPos2d(x, y)
#                ww, wh = image.size
                glDrawPixels(ww, hh, GL_LUMINANCE, GL_UNSIGNED_BYTE, image.tostring())

        return ww, hh, origin, renderer

    def render_text_chunk_tex(self, text, size, orientation='h', cache={}):
        """Render a text chunk using mathtext"""
        size = int(round(size))
#        if (text, size, orientation) in cache and not self.plot.ps:
#            ww, hh, origin, listno =  cache[text, size, orientation]
#            def renderer(x, y):
#                glRasterPos2d(x, y)
#                glCallList(listno)
#            return ww, hh, origin, renderer
        
        if self.plot.ps:
            w, h, _, pswriter = mathtext.math_parse_s_ps(text, 75, size)
            origin = 0
        else:
            w, h, origin, fonts = mathtext.math_parse_s_ft2font(text, 75, size)

        if orientation == 'v': 
            ww, hh, angle = h, w, 90
        else: 
            ww, hh, angle = w, h, 0

        def renderer(x, y):
            if self.plot.ps:
                txt = pswriter.getvalue()
                ps = "gsave\n%f %f translate\n%f rotate\n%s\ngrestore\n" \
                        % ((self.plot.marginl+x)*self.plot.res,
                           (self.plot.marginb+y)*self.plot.res, 
                           angle, txt)
                self.plot.pstext.append(ps)
            else:
                w, h, imgstr = fonts[0].image_as_str()
                N = w*h
                Xall = zeros((N,len(fonts)), dtype=UnsignedInt8)

                for i, f in enumerate(fonts):
                    if orientation == 'v':
                        f.horiz_image_to_vert_image()
                    w, h, imgstr = f.image_as_str()
                    Xall[:,i] = fromstring(imgstr, UnsignedInt8)

                Xs = mlab.max(Xall, 1)
                Xs.shape = (h, w)

                pa = zeros(shape=(h,w,4), dtype=UnsignedInt8)
                rgb = (0., 0., 0.)
                pa[:,:,0] = int(rgb[0]*255)
                pa[:,:,1] = int(rgb[1]*255)
                pa[:,:,2] = int(rgb[2]*255)
                pa[:,:,3] = Xs[::-1]

                data = pa.tostring()

                # clear cache
                if len(cache) >= 20:
                    for key, value in cache.iteritems():
                        _, _, _, listno = value
                        glDeleteLists(listno, 1)
                    cache.clear()

#                listno = glGenLists(1)
                glRasterPos2d(x, y)
#                glNewList(listno, GL_COMPILE)
                glDrawPixels(w, h, GL_RGBA, GL_UNSIGNED_BYTE, data)
#                glEndList()
#                glCallList(listno)
#                cache[text, size, orientation] = ww, hh, origin, listno

        return ww, hh, origin, renderer

    def render_text(self, text, size, x, y, align_x='center', align_y='center', 
                    orientation='h', measure_only=False):
        if '\n' not in text:
            return self.render_text_line(text, size, x, y, align_x, align_y, orientation, measure_only)

        lines = text.splitlines()

        heights = []
        widths = []

        for line in lines:
            w, h = self.render_text_line(line, size, x, y, align_x, align_y, orientation, measure_only=True)
            heights.append(h)
            widths.append(w)

        if orientation == 'h':
            totalh = sum(heights)
            totalw = max(widths)
        elif orientation=='v':
            totalh = max(heights)
            totalw = sum(widths)

        for line, off in zip(lines, [0]+list(cumsum(heights))[:-1]):
            self.render_text_line(line, size, x, y-off, align_x, align_y, orientation)

    def render_text_line(self, text, size, x, y, align_x='center', align_y='center', 
                    orientation='h', measure_only=False):
        if text == '':
            return 0, 0

        t = time.time()

        # split text into chunks
        chunks = cut(text, '$')

        renderers = []
        widths = []
        heights = []
        origins = []
        for chunk, tex in chunks:
            if tex:
                w, h, origin, renderer = self.render_text_chunk_tex('$'+chunk+'$', size, orientation)
                if w!=0 and h!=0:
                    renderers.append(renderer)
                    widths.append(w)
                    heights.append(h)
                    origins.append(origin)
            else:
                chunks2 = cut(chunk, '@')
                for chunk2, at in chunks2:
                    if at:
                        w, h, origin, renderer = self.render_text_chunk_symbol(chunk2, size, orientation)
                    else:
                        w, h, origin, renderer = self.render_text_chunk_normal(chunk2, size, orientation)
                    if w!=0 and h!=0:
                        renderers.append(renderer)
                        widths.append(w)
                        heights.append(h)
                        origins.append(origin)

        #####################################################################
        #                                    ________        _____          #
        #             ___                   | |      |      |     |         #
        #     ___    |   |    ^           __|_|___ _o|      |     |         #
        #    |   |___|   |    |          |    |   |         |_____|         #
        #    |___|___|___|  totalh     __|____|__o|         |     |   ^     #
        #    |o__|   |o__|    |       |       |  |          |     | origin  #
        #        |o__|        v       |_______|_o|          |o____|   v     #
        #                                                                   #
        #####################################################################

        # compute offsets for each chunk and total size 
        if orientation == 'h':
            hb = max(origins)
            ht = max(h-o for h, o in zip(heights, origins))
            totalw, totalh = sum(widths), hb+ht
            offsets = [hb-o for o in origins]
        elif orientation == 'v':
            hb = max(origins)
            ht = max(h-o for h, o in zip(widths, origins))
            totalw, totalh = hb+ht, sum(heights)
            if self.plot.ps:
                offsets = [ht-v-totalw for v in (h-o for h, o in zip(widths, origins))]
            else:
                offsets = [v-ht for v in (h-o for h, o in zip(widths, origins))]

        if measure_only:
            # return width and height of text, in mm
            return totalw/self.plot.res, totalh/self.plot.res

        # alignment (no change = bottom left)
        if align_x == 'right': 
            x -= totalw/self.plot.res
        elif align_x == 'center': 
            x -= (totalw/2)/self.plot.res

        if align_y == 'top': 
            y -= totalh/self.plot.res
        elif align_y == 'center': 
            y -= (totalh/2)/self.plot.res


        # render chunks
        if orientation == 'h':
            for rend, pos, off in zip(renderers, [0]+list(cumsum(widths)/self.plot.res)[:-1], offsets):
                rend(x+pos, y+off/self.plot.res)
        elif orientation == 'v':
            for rend, pos, off in zip(renderers, [0]+list(cumsum(heights)/self.plot.res)[:-1], offsets):
                rend(x-off/self.plot.res, y+pos)

# from matplotlib
def encodeTTFasPS(fontfile):
    """
    Encode a TrueType font file for embedding in a PS file.
    """
    font = file(fontfile, 'rb')
    hexdata, data = [], font.read(65520)
    b2a_hex = binascii.b2a_hex
    while data:
        hexdata.append('<%s>\n' %
                       '\n'.join([b2a_hex(data[j:j+36]).upper()
                                  for j in range(0, len(data), 36)]) )
        data  = font.read(65520)

    hexdata = ''.join(hexdata)[:-2] + '00>'
    font    = FT2Font(str(fontfile))

    headtab  = font.get_sfnt_table('head')
    version  = '%d.%d' % headtab['version']
    revision = '%d.%d' % headtab['fontRevision']

    dictsize = 8
    fontname = font.postscript_name
    encoding = 'StandardEncoding'
    fontbbox = '[%d %d %d %d]' % font.bbox

    posttab  = font.get_sfnt_table('post')
    minmemory= posttab['minMemType42']
    maxmemory= posttab['maxMemType42']

    infosize = 7
    sfnt     = font.get_sfnt()
    notice   = sfnt[(1,0,0,0)]
    family   = sfnt[(1,0,0,1)]
    fullname = sfnt[(1,0,0,4)]
    iversion = sfnt[(1,0,0,5)]
    fixpitch = str(bool(posttab['isFixedPitch'])).lower()
    ulinepos = posttab['underlinePosition']
    ulinethk = posttab['underlineThickness']
    italicang= '(%d.%d)' % posttab['italicAngle']

    numglyphs = font.num_glyphs
    glyphs = []
    for j in range(numglyphs):
        glyphs.append('/%s %d def' % (font.get_glyph_name(j), j))
        if j != 0 and j%4 == 0:
            glyphs.append('\n')
        else:
            glyphs.append(' ')
    glyphs = ''.join(glyphs)
    data = ['%%!PS-TrueType-%(version)s-%(revision)s\n' % locals()]
    if maxmemory:
        data.append('%%%%VMusage: %(minmemory)d %(maxmemory)d' % locals())
    data.append("""%(dictsize)d dict begin
/FontName /%(fontname)s def
/FontMatrix [1 0 0 1 0 0] def
/FontType 42 def
/Encoding %(encoding)s def
/FontBBox %(fontbbox)s def
/PaintType 0 def
/FontInfo %(infosize)d dict dup begin
/Notice (%(notice)s) def
/FamilyName (%(family)s) def
/FullName (%(fullname)s) def
/version (%(iversion)s) def
/isFixedPitch %(fixpitch)s def
/UnderlinePosition %(ulinepos)s def
/UnderlineThickness %(ulinethk)s def
end readonly def
/sfnts [
%(hexdata)s
] def
/CharStrings %(numglyphs)d dict dup begin
%(glyphs)s
end readonly def
FontName currentdict end definefont pop""" % locals())
    return ''.join(data)

