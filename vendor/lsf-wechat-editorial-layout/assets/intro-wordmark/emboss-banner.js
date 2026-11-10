import { EMBOSS_VERT, EMBOSS_FRAG } from '../design-how/emboss/assets/template/shaders';
import plaster from '../design-how/emboss/assets/media/vault/emboss-plaster.webp';
import grunge from '../design-how/emboss/assets/media/vault/emboss-grunge.webp';

const fragment = EMBOSS_FRAG
  .replace('vec2(0.347, 0.653)', 'vec2(0.0, 1.0)')
  .replace('if (x >= P0.x && x <= P0.y) return 0;', '')
  .replace('if (x >= P2.x && x <= P2.y) return 2;', '')
  .replace('const float PY0 = 0.16;', 'const float PY0 = 0.0;')
  .replace('const float PY1 = 0.84;', 'const float PY1 = 1.0;')
  .replace('float edge = smoothstep(0.0, RADIUS, min(edgeX, edgeY));', 'float edge = 1.0;');
const duration = 2400;
const fullTurn = 2 * Math.PI;
const media = [plaster, grunge].map(src => {
  const image = new Image();
  image.src = src;
  return image;
});
export const embossReady = Promise.allSettled(media.map(image => image.decode()));

function createProgram(gl) {
  const program = gl.createProgram();
  for (const [type, source] of [[gl.VERTEX_SHADER, EMBOSS_VERT], [gl.FRAGMENT_SHADER, fragment]]) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
    gl.attachShader(program, shader);
    gl.deleteShader(shader);
  }
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  return program;
}

function paintMask(context, { width, height }, { logo, text, fontFamily }) {
  if (logo) {
    const scale = Math.min(width * .69 / logo.naturalWidth, height * .64 / logo.naturalHeight);
    const w = logo.naturalWidth * scale, h = logo.naturalHeight * scale;
    context.drawImage(logo, (width - w) / 2, (height - h) / 2, w, h);
    return;
  }
  context.font = `800 ${Math.round(height * .35)}px ${fontFamily}`;
  context.textAlign = 'center';
  context.textBaseline = 'middle';
  context.fillStyle = '#fff';
  context.fillText(String(text), width / 2, height / 2, width * .78);
}

function buildField(width, height, props) {
  const crisp = Object.assign(document.createElement('canvas'), { width, height });
  const blurred = Object.assign(document.createElement('canvas'), { width, height });
  const cx = crisp.getContext('2d', { willReadFrequently: true });
  const bx = blurred.getContext('2d', { willReadFrequently: true });
  paintMask(cx, crisp, props);
  bx.filter = `blur(${Math.max(.8, height * .014)}px)`;
  bx.drawImage(crisp, 0, 0);
  const c = cx.getImageData(0, 0, width, height).data;
  const b = bx.getImageData(0, 0, width, height).data;
  const packed = cx.createImageData(width, height);
  for (let index = 0; index < c.length; index += 4) {
    packed.data[index] = c[index + 3];
    packed.data[index + 1] = b[index + 3];
    packed.data[index + 3] = 255;
  }
  return packed;
}

export function createEmbossBanner(canvas, initial) {
  const surface = document.createElement('canvas');
  const output = canvas.getContext('2d');
  const gl = surface.getContext('webgl', { alpha: false });
  if (!gl) throw new Error('Emboss requires WebGL');
  const program = createProgram(gl);
  const buffer = gl.createBuffer();
  const textures = [gl.createTexture(), gl.createTexture(), gl.createTexture()];
  const uniforms = new Map();
  const set = (name, type, ...args) => {
    if (!uniforms.has(name)) uniforms.set(name, gl.getUniformLocation(program, name));
    gl[type](uniforms.get(name), ...args);
  };
  const texture = index => {
    gl.activeTexture(gl.TEXTURE0 + index);
    gl.bindTexture(gl.TEXTURE_2D, textures[index]);
  };
  gl.useProgram(program);
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,0,1, 1,-1,1,1, -1,1,0,0, 1,1,1,0]), gl.STATIC_DRAW);
  for (const [name, offset] of [['aPosition', 0], ['aUV', 8]]) {
    const attr = gl.getAttribLocation(program, name);
    gl.enableVertexAttribArray(attr);
    gl.vertexAttribPointer(attr, 2, gl.FLOAT, false, 16, offset);
  }
  for (const [index, name] of ['uField','uPlaster','uGrunge'].entries()) {
    texture(index);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([156,156,156,255]));
    set(name, 'uniform1i', index);
  }
  set('uDepth', 'uniform3f', 1.9, 1.9, 1.9);
  set('uHi', 'uniform3f', .67, .67, .67);
  set('uSh', 'uniform3f', .46, .46, .46);
  set('uContrast', 'uniform3f', .55, .55, .55);
  set('uBright', 'uniform3f', 1.56, 1.56, 1.56);
  set('uTint1', 'uniform3f', .90, .84, 1.0);
  set('uTexScale', 'uniform3f', 1.4, 1.4, 1.4);
  set('uTexOff1', 'uniform2f', .4, .45);
  set('uLightZ', 'uniform1f', .48);
  set('uGrungeAmt', 'uniform1f', .38);
  set('uHover', 'uniform1f', -1);
  set('uReveal', 'uniform1f', 1);

  let props = {};
  let destroyed = false;
  const upload = (index, image) => {
    texture(index);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
  };
  function draw(time) {
    if (destroyed || gl.isContextLost()) return;
    const phase = props.reducedMotion ? 0 : time / duration * fullTurn;
    const angle = 73 * Math.PI / 180 + Math.sin(phase) * .37;
    set('uLight', 'uniform2f', Math.cos(angle), -Math.sin(angle));
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    output.drawImage(surface, 0, 0);
  }
  function update(next) {
    const sizeChanged = (next.width && next.width !== canvas.width)
      || (next.height && next.height !== canvas.height);
    const contentChanged = next.text !== props.text || next.logo !== props.logo || next.fontFamily !== props.fontFamily;
    props = { ...props, ...next };
    if (sizeChanged || !surface.dataset.ready) {
      canvas.width = surface.width = props.width || canvas.width;
      canvas.height = surface.height = props.height || canvas.height;
      gl.viewport(0, 0, canvas.width, canvas.height);
      set('uTexel', 'uniform2f', 1 / canvas.width, 1 / canvas.height);
      surface.dataset.ready = 'true';
    }
    if (sizeChanged || contentChanged) upload(0, buildField(canvas.width, canvas.height, props));
  }
  update(initial);
  embossReady.then(() => {
    if (destroyed) return;
    media.forEach((image, index) => {
      if (image.naturalWidth) upload(index + 1, image);
    });
    if (props.reducedMotion) draw(0);
  });
  return {
    update, draw, duration: () => duration,
    destroy() {
      destroyed = true;
      textures.forEach(item => gl.deleteTexture(item));
      gl.deleteBuffer(buffer);
      gl.deleteProgram(program);
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    },
  };
}

export async function prepareLogo(file) {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 12 * 1024 * 1024) {
    throw new Error('请选择 12 MB 以内的 PNG、JPG 或 WebP');
  }
  const bitmap = await createImageBitmap(file);
  try {
    const scale = Math.min(1, 440 / Math.max(bitmap.width, bitmap.height));
    const width = Math.max(1, Math.round(bitmap.width * scale));
    const height = Math.max(1, Math.round(bitmap.height * scale));
    const canvas = Object.assign(document.createElement('canvas'), { width, height });
    const context = canvas.getContext('2d', { willReadFrequently: true });
    context.drawImage(bitmap, 0, 0, width, height);
    const pixels = context.getImageData(0, 0, width, height);
    const data = pixels.data;
    let transparent = 0;
    for (let i = 3; i < data.length; i += 4) if (data[i] < 32) transparent++;
    if (transparent < width * height * .01) {
      const corners = [0, (width - 1) * 4, (height - 1) * width * 4, (width * height - 1) * 4];
      const color = [0, 1, 2].map(channel => corners.reduce((sum, i) => sum + data[i + channel], 0) / corners.length);
      let marked = 0;
      for (let i = 0; i < data.length; i += 4) {
        const diff = Math.hypot(data[i] - color[0], data[i + 1] - color[1], data[i + 2] - color[2]);
        data[i + 3] = Math.round(Math.max(0, Math.min(1, (diff - 24) / 92)) * 255);
        if (data[i + 3] > 80) marked++;
      }
      if (marked < width * height * .003) throw new Error('没有识别到 Logo 轮廓，请试试透明底 PNG');
      context.putImageData(pixels, 0, 0);
    }
    return canvas.toDataURL('image/png');
  } finally {
    bitmap.close();
  }
}
