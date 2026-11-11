import re
import sys
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

def cubic_bezier(p0, p1, p2, p3, steps=20):
    points = []
    for i in range(steps + 1):
        t = i / steps
        it = 1 - t
        x = (it**3) * p0[0] + 3 * (it**2) * t * p1[0] + 3 * it * (t**2) * p2[0] + (t**3) * p3[0]
        y = (it**3) * p0[1] + 3 * (it**2) * t * p1[1] + 3 * it * (t**2) * p2[1] + (t**3) * p3[1]
        points.append((x, y))
    return points

def parse_svg_path_to_points(d, scale=1.0):
    tokens = re.findall(r'([A-Za-z])|([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)', d)
    points = []
    current_pt = (0.0, 0.0)
    cmd = None
    nums = []
    
    parsed_cmds = []
    for t_cmd, t_num in tokens:
        if t_cmd:
            if cmd and nums:
                parsed_cmds.append((cmd, [float(x) for x in nums]))
            cmd = t_cmd
            nums = []
        elif t_num:
            nums.append(t_num)
    if cmd and nums:
        parsed_cmds.append((cmd, [float(x) for x in nums]))
        
    poly_segments = []
    current_seg = []
    
    for c, args in parsed_cmds:
        if c == 'M':
            if len(args) >= 2:
                current_pt = (args[0] * scale, args[1] * scale)
                if current_seg:
                    poly_segments.append(current_seg)
                current_seg = [current_pt]
                # If multiple pairs in M, subsequent are L
                for i in range(2, len(args), 2):
                    current_pt = (args[i] * scale, args[i+1] * scale)
                    current_seg.append(current_pt)
        elif c == 'L':
            for i in range(0, len(args), 2):
                current_pt = (args[i] * scale, args[i+1] * scale)
                current_seg.append(current_pt)
        elif c == 'C':
            for i in range(0, len(args), 6):
                p0 = current_pt
                p1 = (args[i] * scale, args[i+1] * scale)
                p2 = (args[i+2] * scale, args[i+3] * scale)
                p3 = (args[i+4] * scale, args[i+5] * scale)
                pts = cubic_bezier(p0, p1, p2, p3)
                current_seg.extend(pts[1:])
                current_pt = p3
        elif c in ('Z', 'z'):
            if current_seg and len(current_seg) > 1:
                current_seg.append(current_seg[0])
                poly_segments.append(current_seg)
                current_seg = []

    if current_seg:
        poly_segments.append(current_seg)
        
    return poly_segments

def render_svg_to_png(svg_path, png_path, scale=2):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    view_box = root.attrib.get('viewBox', '').split()
    if view_box and len(view_box) >= 4:
        vw = float(view_box[2])
        vh = float(view_box[3])
    else:
        vw = float(root.attrib.get('width', 800))
        vh = float(root.attrib.get('height', 800))
        
    width = int(vw * scale)
    height = int(vh * scale)
    
    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    font_cache = {}
    def get_font(size, weight):
        size = int(size * scale)
        is_bold = (weight == 'bold')
        key = (size, is_bold)
        if key not in font_cache:
            font_file = 'C:/Windows/Fonts/arialbd.ttf' if is_bold else 'C:/Windows/Fonts/arial.ttf'
            try:
                font_cache[key] = ImageFont.truetype(font_file, size)
            except:
                font_cache[key] = ImageFont.load_default()
        return font_cache[key]

    def parse_color(c):
        if not c or c == 'none' or c == '#00000000':
            return None
        c = c.strip()
        if c.startswith('#'):
            if len(c) == 4:
                return (int(c[1], 16) * 17, int(c[2], 16) * 17, int(c[3], 16) * 17)
            elif len(c) == 7:
                return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
            elif len(c) == 9:
                return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16))
        return (0, 0, 0)

    def parse_style(style_str):
        if not style_str:
            return {}
        result = {}
        for part in style_str.split(';'):
            part = part.strip()
            if ':' in part:
                k, v = part.split(':', 1)
                result[k.strip()] = v.strip()
        return result

    def get_style(elem):
        if 'style' in elem.attrib:
            return parse_style(elem.attrib['style'])
        return {}

    def get_attr(elem, name, default=None):
        if name in elem.attrib:
            return elem.attrib[name]
        style = get_style(elem)
        if name in style:
            return style[name]
        return default

    def get_fill(elem):
        fill = get_attr(elem, 'fill', 'none')
        if fill == 'none':
            return None
        return parse_color(fill)

    def get_stroke(elem):
        stroke = get_attr(elem, 'stroke', 'none')
        if stroke == 'none':
            return None
        return parse_color(stroke)

    def get_stroke_width(elem):
        sw = get_attr(elem, 'stroke-width', '1')
        try:
            return float(sw) * scale
        except:
            return scale

    def get_stroke_dasharray(elem):
        return get_attr(elem, 'stroke-dasharray', '')

    def get_fill_opacity(elem):
        try:
            return float(get_attr(elem, 'fill-opacity', '1'))
        except:
            return 1.0

    def get_font_size(elem):
        try:
            return float(get_attr(elem, 'font-size', '11'))
        except:
            return 11.0

    def get_font_weight(elem):
        return get_attr(elem, 'font-weight', 'normal')

    def parse_dasharray(val):
        if not val:
            return None
        parts = re.split(r'[,\s]+', val.strip())
        try:
            return [float(p) for p in parts if p]
        except ValueError:
            return None

    def draw_dashed_line(draw, x1, y1, x2, y2, fill, width, dasharray, scale=1):
        dx = x2 - x1
        dy = y2 - y1
        total_len = (dx ** 2 + dy ** 2) ** 0.5
        if total_len == 0:
            return
        ux, uy = dx / total_len, dy / total_len
        dist = 0.0
        dash_idx = 0
        while dist < total_len:
            dash_len = dasharray[dash_idx % len(dasharray)]
            seg_start = dist
            seg_end = min(dist + dash_len, total_len)
            p1 = (x1 + seg_start * ux, y1 + seg_start * uy)
            p2 = (x1 + seg_end * ux, y1 + seg_end * uy)
            draw.line([p1, p2], fill=fill, width=width)
            dist = seg_end
            dash_idx += 1

    for elem in root.iter():
        tag = elem.tag.split('}')[-1]
        
        fill = get_fill(elem)
        stroke = get_stroke(elem)
        sw = max(1, int(round(get_stroke_width(elem))))
        fill_opacity = get_fill_opacity(elem)
        has_fill = fill and fill_opacity > 0.01
        has_stroke = stroke is not None
        
        if tag == 'rect':
            x = float(get_attr(elem, 'x', '0')) * scale
            y = float(get_attr(elem, 'y', '0')) * scale
            w = float(get_attr(elem, 'width', '0')) * scale
            h = float(get_attr(elem, 'height', '0')) * scale
            rx = float(get_attr(elem, 'rx', '0')) * scale
            ry = float(get_attr(elem, 'ry', '0')) * scale

            if has_fill or has_stroke:
                if rx > 0:
                    draw.rounded_rectangle([x, y, x + w, y + h], radius=int(rx),
                                           fill=fill if has_fill else None,
                                           outline=stroke if has_stroke else None,
                                           width=sw if has_stroke else 0)
                else:
                    draw.rectangle([x, y, x + w, y + h],
                                   fill=fill if has_fill else None,
                                   outline=stroke if has_stroke else None,
                                   width=sw if has_stroke else 0)
                     
        elif tag == 'ellipse' or tag == 'circle':
            if tag == 'circle':
                cx = float(get_attr(elem, 'cx', '0')) * scale
                cy = float(get_attr(elem, 'cy', '0')) * scale
                r = float(get_attr(elem, 'r', '0')) * scale
                rx, ry = r, r
            else:
                cx = float(get_attr(elem, 'cx', '0')) * scale
                cy = float(get_attr(elem, 'cy', '0')) * scale
                rx = float(get_attr(elem, 'rx', '0')) * scale
                ry = float(get_attr(elem, 'ry', '0')) * scale
            if has_fill or has_stroke:
                draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                             fill=fill if has_fill else None,
                             outline=stroke if has_stroke else None,
                             width=sw if has_stroke else 0)
                 
        elif tag == 'line':
            x1 = float(get_attr(elem, 'x1', '0')) * scale
            y1 = float(get_attr(elem, 'y1', '0')) * scale
            x2 = float(get_attr(elem, 'x2', '0')) * scale
            y2 = float(get_attr(elem, 'y2', '0')) * scale
            if has_stroke:
                dash = parse_dasharray(get_stroke_dasharray(elem))
                if dash:
                    draw_dashed_line(draw, x1, y1, x2, y2, stroke, sw, dash, scale)
                else:
                    draw.line([x1, y1, x2, y2], fill=stroke, width=sw)
                 
        elif tag == 'polygon':
            pts_str = get_attr(elem, 'points', '')
            pts = []
            for p in pts_str.strip().split():
                if ',' in p:
                    parts = p.split(',')
                    if len(parts) >= 2:
                        try:
                            px = float(parts[0]) * scale
                            py = float(parts[1]) * scale
                            pts.append((px, py))
                        except ValueError:
                            pass
            if len(pts) >= 2:
                if has_fill:
                    draw.polygon(pts, fill=fill)
                if has_stroke:
                    draw.polygon(pts, outline=stroke, width=sw)
                     
        elif tag == 'path':
            d = get_attr(elem, 'd', '')
            if d:
                poly_segments = parse_svg_path_to_points(d, scale=scale)
                for seg in poly_segments:
                    if len(seg) >= 2:
                        if has_fill:
                            draw.polygon(seg, fill=fill)
                        if has_stroke:
                            dash = parse_dasharray(get_stroke_dasharray(elem))
                            if dash:
                                for i in range(len(seg) - 1):
                                    draw_dashed_line(draw, seg[i][0], seg[i][1], seg[i+1][0], seg[i+1][1], stroke, sw, dash, scale)
                            else:
                                draw.line(seg, fill=stroke, width=sw)
        
        elif tag == 'text':
            content = elem.text or ''
            if content.strip():
                tx = float(get_attr(elem, 'x', '0')) * scale
                ty = float(get_attr(elem, 'y', '0')) * scale
                fsize = get_font_size(elem)
                fweight = get_font_weight(elem)
                font = get_font(fsize, fweight)
                text_color = get_fill(elem) or (0, 0, 0)
                draw.text((tx, ty - fsize * scale * 0.82), content, font=font, fill=text_color)
                 
    img.save(png_path, 'PNG', optimize=True)
    print(f"Successfully saved {png_path} ({width}x{height})")

if __name__ == '__main__':
    svg_file = sys.argv[1] if len(sys.argv) > 1 else 'references/bab 4/ERD_PIXELT_FINAL.svg'
    png_file = sys.argv[2] if len(sys.argv) > 2 else 'references/bab 4/ERD_PIXELT_FINAL.png'
    render_svg_to_png(svg_file, png_file, scale=2)

