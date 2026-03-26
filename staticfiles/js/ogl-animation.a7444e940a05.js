import {
  Renderer,
  Transform,
  Mesh,
  Program,
  Vec2,
  Vec3,
  Texture,
  RenderTarget,
  Triangle,
  Geometry
  
} from "https://esm.sh/ogl";

function generateRandomTexture(width, height) {
  const data = new Float32Array(width * height * 4); 
  
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const index = (y * width + x) * 4;
      data[index] = Math.random();
      data[index + 1] = Math.random();
      data[index + 2] = 0;
      data[index + 3] = 0;
    }
  }

  return data;
}
class SplatSimulation {
  constructor(renderer) {
    this.renderer = renderer;

    const gl = this.renderer.gl;

    this.uniform = { value: null };

    this.scene = new Transform();

    this.width = 0;
    this.height = 0;

    const options = {
      width: 2,
      height: 2,
      type: gl.HALF_FLOAT,
      format: gl.RGBA,
      internalFormat: gl.RGBA16F,
      minFilter: gl.LINEAR,
      depth: false
    };

    this.fbo = {
      read: new RenderTarget(gl, options),
      write: new RenderTarget(gl, options),
      swap: () => {
        let temp = this.fbo.read;
        this.fbo.read = this.fbo.write;
        this.fbo.write = temp;
      }
    };

    this.splatPos = new Vec2();
    this.splatPrevPos = new Vec2();
    this.splatVelocity = 0;
    this.splatTargetVelocity = 0;

    this.lastTime = 0;
    this.lastMoveTime = 0;

    this.createFSQuad();
  }

  createFSQuad() {
    const gl = this.renderer.gl;

    const vertex = `#version 300 es
      in vec2 uv;
      in vec3 position;
      out vec2 vUv;

      void main() {
        vUv = uv;
        gl_Position = vec4(position, 1.0);
      }
    `;

    const fragment = `#version 300 es
      precision highp float;
      in vec2 vUv;
      out vec4 fragColor;

      uniform sampler2D tBuffer;
      uniform sampler2D tAdvect;
      uniform vec2 uSplatCoords;
      uniform vec2 uSplatPrevCoords;
      uniform float uSplatRadius;

      float cubicIn(float t) { return t * t * t; }

      float line(vec2 uv, vec2 point1, vec2 point2) {
          vec2 pa = uv - point1, ba = point2 - point1;
          float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
          return length(pa - ba * h);
      }

      void main() {
        vec2 uv = vUv;

        vec2 invResolution = 1.0 / vec2(textureSize(tBuffer, 0));

        vec2 advect = (texture(tAdvect, uv * 3.0).xy * 2.0 - 1.0) * 1.0;
        uv += advect * invResolution;

        float wavespeed = 1.0;
        vec2 offset = invResolution * wavespeed;
        float l = texture(tBuffer, uv - vec2(offset.x, 0.0)).r;
        float r = texture(tBuffer, uv + vec2(offset.x, 0.0)).r;
        float t = texture(tBuffer, uv + vec2(0.0, offset.y)).r;
        float b = texture(tBuffer, uv - vec2(0.0, offset.y)).r;
        float nextVal = max(max(max(l, r), t), b);

        float radius = 0.05 * smoothstep(0.1, 1.0, uSplatRadius);
        float splat = cubicIn(clamp(1.0 - line(vUv, uSplatPrevCoords.xy, uSplatCoords.xy) / radius, 0.0, 1.0));
        nextVal += splat;

        nextVal *= 0.985;
        nextVal = min(nextVal, 1.0);

        vec4 prev = texture(tBuffer, uv);
        float rim = nextVal - prev.r;

        float rimLerp = prev.b + rim;
        rimLerp *= 0.9;

        fragColor = vec4(nextVal, rim, rimLerp, 1.0);
      }
    `;

    const noiseTexture = new Texture(gl, {
      image: generateRandomTexture(256, 256),
      target: gl.TEXTURE_2D,
      format: gl.RGBA,
      type: gl.FLOAT,
      internalFormat: gl.RGBA32F,
      width: 256,
      height: 256,
      wrapS: gl.REPEAT,
      wrapT: gl.REPEAT,
      magFilter: gl.LINEAR,
      minFilter: gl.LINEAR
    });

    this.fsProgram = new Program(gl, {
      vertex,
      fragment,                                                                         
      uniforms: {                                                                         
        tBuffer: { value: null },                                                                         
        tAdvect: { value: noiseTexture },                                                                         
        uSplatCoords: { value: this.splatPos },                                                                         
        uSplatPrevCoords: { value: this.splatPrevPos },                                                                         
        uSplatRadius: { value: this.splatVelocity }                                                                         
      },                                                                          
      depthTest: false,                                                                         
      depthWrite: false                                                                         
    });                                                                         

    const geometry = new Triangle(gl);                                                                          
    this.fsQuad = new Mesh(gl, { geometry, program: this.fsProgram });                                                                          
  }                                                                         

  onPointerMove({ x, y }) {                                                                         
    this.splatPos.set(x / this.width, 1.0 - y / this.height);                                                                         
  }

  resize() {
    const w = this.renderer.width;
    const h = this.renderer.height;

    this.width = w;
    this.height = h;

    const rtw = w / 5;
    const rth = h / 5;
    this.fbo.read.setSize(rtw, rth);
    this.fbo.write.setSize(rtw, rth);
  }

  update = () => {
    const f = performance.now() / 1000;
    if (f - this.lastTime < 0.015) return;
    this.lastTime = f;

    let dist = this.splatPos.distance(this.splatPrevPos);
    const timeSinceMove = f - this.lastMoveTime;
    if (dist > 0) this.lastMoveTime = f;
    if (timeSinceMove > 0.15 || dist > 0.3) {
      this.splatPrevPos.copy(this.splatPos);
      this.splatTargetVelocity = 0;
      dist = 0;
    }

    this.splatTargetVelocity += dist * 6;
    this.splatTargetVelocity *= 0.88;
    this.splatTargetVelocity = Math.min(this.splatTargetVelocity, 1);
    this.splatVelocity += (this.splatTargetVelocity - this.splatVelocity) * 0.1;

    this.fsProgram.uniforms.uSplatRadius.value = this.splatVelocity;
    this.fsProgram.uniforms.tBuffer.value = this.fbo.read.texture;

    this.renderer.render({
      scene: this.fsQuad,
      target: this.fbo.write,
      clear: false
    });

    this.splatPrevPos.copy(this.splatPos);

    this.uniform.value = this.fbo.write.texture;

    this.fbo.swap();
  };
}

const colors = [
  [0.10196078431372549, 0.7372549019607844, 0.611764705882353],
  [0.1803921568627451, 0.8, 0.44313725490196076],
  [0.20392156862745098, 0.596078431372549, 0.8588235294117647],
  [0.6078431372549019, 0.34901960784313724, 0.7137254901960784],
  [0.20392156862745098, 0.28627450980392155, 0.3686274509803922],
  [0.08627450980392157, 0.6274509803921569, 0.5215686274509804],
  [0.15294117647058825, 0.6823529411764706, 0.3764705882352941],
  [0.1607843137254902, 0.5019607843137255, 0.7254901960784313],
  [0.5568627450980392, 0.26666666666666666, 0.6784313725490196],
  [0.17254901960784313, 0.24313725490196078, 0.3137254901960784],
  [0.9450980392156862, 0.7686274509803922, 0.058823529411764705],
  [0.9019607843137255, 0.49411764705882355, 0.13333333333333333],
  [0.9058823529411765, 0.2980392156862745, 0.23529411764705882],
  [0.9254901960784314, 0.9411764705882353, 0.9450980392156862],
  [0.9529411764705882, 0.611764705882353, 0.07058823529411765],
  [0.8274509803921568, 0.3294117640588235, 0],
  [0.7529411764705882, 0.2235294117647059, 0.16862745098039217],
  [0.996078431372549, 0.6823529411764706, 0.7372549019607844]
];

const colorVertex = `#version 300 es
  precision highp float;

  in vec2 uv;
  in vec2 position;

  out vec2 vUv;

  void main() {
      vUv = uv;
      gl_Position = vec4(position, 0, 1);
  }
`;

const colorFragment = `#version 300 es
precision highp float;

uniform sampler2D tSim;
uniform sampler2D tMap;
uniform sampler2D tRandom;
uniform vec2 uResolution;
uniform vec3 uColors[18];

in vec2 vUv;
out vec4 fragColor;

float rand(vec2 co) {
    return fract(sin(dot(co, vec2(12.9898,78.233))) * 43758.5453);
}

void main() {
    float rnd = texture(tRandom, vUv).r;
    vec4 prev = texture(tMap, vUv);
    vec4 sim  = texture(tSim, vUv);

    vec3 color = prev.rgb;
    float phase = prev.a;

    if (sim.r * sim.g >= 0.05 && prev.r == 1. && rand(vUv * sim.rb * rnd) < 0.2) {
        int idx = int(floor(rand(vUv * sim.rg * rnd) * 18.0));
        color = uColors[idx];
        phase = 2.0 * sim.r;
    } else {
      if (phase < 0.6 * rnd && color.r != 1.) {
        color = vec3(1.0, 1.0, 1.0);
        phase = rnd * phase;
      }
    }

    if (color.r == 1.) {
      phase = fract(phase + 0.005 + rand(vUv * rnd) * 0.005);
    } else {
      phase *= 0.98;
    }

    fragColor = vec4(color, phase);
}`;

const vertex = `#version 300 es

precision highp float;

in vec2 uv;
in vec2 position;

uniform mat4 modelViewMatrix;
uniform mat4 projectionMatrix;
uniform mat3 normalMatrix;
uniform int uRows;
uniform int uColumns;
uniform vec2 uResolution;
uniform float uSize;
uniform float uGap;
uniform float uTime;
uniform sampler2D tColor;
uniform sampler2D tSim;

out vec2 vUv;
flat out vec4 vColor;

float rand(vec2 co) {
    return fract(sin(dot(co, vec2(12.9898,78.233))) * 43758.5453);
}

void main() {
    int row = gl_InstanceID / uColumns;
    int col = gl_InstanceID % uColumns;
    int invRow = (uRows - 1) - row;

    vec2 pxToClip = 2.0 / uResolution;

    float stepX = uSize + uGap;
    float stepY = uSize + uGap;

    float cellX = float(col) * stepX;
    float cellY = float(invRow) * stepY;

    vec2 pos = position * (uSize * 0.5) * pxToClip;

    vec2 offset = vec2(cellX, -cellY) * pxToClip;

    vec2 topLeft = vec2(-1.0 + uSize * 0.5 * pxToClip.x, 1.0 - uSize * 0.5 * pxToClip.y);

    vUv = (vec2(col, row) + 1.) / (vec2(float(uColumns), float(uRows)) + 1.);
    vec4 c = texture(tColor, vUv);

    if (c.r == 1.) {
      float alpha = mix(.1, 0.2, step(0.75, c.a));
      c.a = alpha;
    }

    vColor = c;

    gl_Position = vec4(pos + offset + topLeft, 0., 1.);
}
`;

const fragment = `#version 300 es
precision highp float;

in vec2 vUv;
flat in vec4 vColor;
out vec4 fragColor;

void main() {
    vec4 c = vColor;

    fragColor = c;
}`;

const size = 4;
const space = 2;
const resolution = { value: [0, 0] };
const renderer = new Renderer({
  dpr: window.devicePixelRatio,
  alpha: true
});
const gl = renderer.gl;
const time = { value: 0 };
const mouse = {
  x: 0,
  y: 0,
  smoothX: 0,
  smoothY: 0
};

const simulation = new SplatSimulation(renderer);

document.querySelector("[data-app-container]").appendChild(gl.canvas);
gl.clearColor(0, 0, 0, 0);

function resize() {
  const w = window.innerWidth;
  const h = window.innerHeight;

  renderer.setSize(w, h);
  resolution.value = [w, h];
  simulation.resize();
}
window.addEventListener("resize", resize, false);
resize();

const scene = new Transform();

const columns = Math.ceil((renderer.width + space) / (size + space));
const rows = Math.ceil((renderer.height + space) / (size + space));
const cells = columns * rows;

function onMouseMove(e) {
  mouse.x = e.clientX;
  mouse.y = e.clientY;
}

window.addEventListener(
  "pointermove",
  (e) => {
    cancelManualMove();
    onMouseMove(e);
    mouse.smoothX = mouse.x;
    mouse.smoothY = mouse.y;
    window.addEventListener("pointermove", onMouseMove);
  },
  {
    once: true
  }
);

function onTouch(e) {
  onMouseMove(e.touches[0]);
}
window.addEventListener("touchmove", onTouch);
window.addEventListener("touchstart", (e) => {
  e.preventDefault();

  cancelManualMove();
  onMouseMove(e.touches[0]);

  mouse.smoothX = mouse.x;
  mouse.smoothY = mouse.y;
});

const initialImageData = new Float32Array(cells * 4);
const initialRandomData = new Float32Array(cells);
for (let i = 0; i < cells; i++) {
  initialRandomData.set([Math.min(Math.random() + 0.2, 0.95)], i);
  initialImageData.set([1, 1, 1, Math.random()], i * 4);
}

const initImageTexture = new Texture(gl, {
  image: initialImageData,
  target: gl.TEXTURE_2D,
  type: gl.FLOAT,
  format: gl.RGBA,
  internalFormat: gl.RGBA32F,
  wrapS: gl.CLAMP_TO_EDGE,
  wrapT: gl.CLAMP_TO_EDGE,
  generateMipmaps: false,
  minFilter: gl.NEAREST,
  magFilter: gl.NEAREST,
  width: columns,
  height: rows,
  flipY: false
});

const colorUniform = { value: initImageTexture };

const colorRandom = {
  value: new Texture(gl, {
    image: initialRandomData,
    target: gl.TEXTURE_2D,
    type: gl.FLOAT,
    format: gl.RED,
    internalFormat: gl.R32F,
    wrapS: gl.CLAMP_TO_EDGE,
    wrapT: gl.CLAMP_TO_EDGE,
    generateMipmaps: false,
    minFilter: gl.NEAREST,
    magFilter: gl.NEAREST,
    width: columns,
    height: rows
  })
};

const colorOptions = {
  width: columns,
  height: rows,
  type: gl.FLOAT,
  format: gl.RGBA,
  internalFormat: gl.RGBA32F,
  minFilter: gl.NEAREST,
  depth: false,
  unpackAlignment: 1
};

const colorFbo = {
  read: new RenderTarget(gl, colorOptions),
  write: new RenderTarget(gl, colorOptions),
  render: () => {
    renderer.render({
      scene: colorMesh,
      target: colorFbo.write,
      clear: false
    });
    colorFbo.swap();
  },
  swap: () => {
    let temp = colorFbo.read;
    colorFbo.read = colorFbo.write;
    colorFbo.write = temp;
    colorUniform.value = colorFbo.read.texture;
  }
};

const colorProgram = new Program(gl, {
  vertex: colorVertex,
  fragment: colorFragment,
  uniforms: {
    tMap: colorUniform,
    tSim: simulation.uniform,
    uResolution: resolution,
    uRows: { value: rows },
    uColumns: { value: columns },
    uSize: { value: cells },
    uColors: {
      value: colors
    },
    tRandom: colorRandom
  }
});
const colorMesh = new Mesh(gl, {
  geometry: new Triangle(gl),
  program: colorProgram
});

const geometry = new Geometry(gl, {
  position: {
    instanced: 0.25,
    size: 2,
    data: new Float32Array([-1, 1, -1, -1, 1, 1, 1, -1])
  },
  uv: { size: 2, data: new Float32Array([0, 1, 0, 0, 1, 1, 1, 0]) },
  index: { data: new Uint16Array([0, 1, 2, 1, 3, 2]) }
});

geometry.setInstancedCount(cells);

const program = new Program(gl, {
  vertex,
  fragment,
  uniforms: {
    uRows: { value: rows },
    uColumns: { value: columns },
    uResolution: resolution,
    uSize: { value: size },
    uGap: { value: space },
    uTime: time,
    tColor: colorUniform,
    tSim: simulation.uniform
  }
});

const points = new Mesh(gl, { geometry, program });
points.setParent(scene);
points.position.set(-1, 1, 0);

requestAnimationFrame(update);
function update(t) {
  requestAnimationFrame(update);

  mouse.smoothX += (mouse.x - mouse.smoothX) * 0.15;
  mouse.smoothY += (mouse.y - mouse.smoothY) * 0.15;
  simulation.onPointerMove({
    x: mouse.smoothX,
    y: mouse.smoothY
  });

  time.value = t;

  simulation.update();
  colorFbo.render();

  renderer.render({ scene });
}

let mID;
function manualMouseMove(t) {
  mID = requestAnimationFrame(manualMouseMove);

  t *= 0.001;
  const width = resolution.value[0];
  const height = resolution.value[1];
  mouse.x = width * 0.5 + Math.cos(t * 2.1) * Math.cos(t * 0.8) * width * 0.5;
  mouse.y =
    height * 0.5 +
    Math.sin(t * 3.1) * Math.tan(Math.sin(t * 0.8)) * height * 0.5;
}
function cancelManualMove() {
  cancelAnimationFrame(mID);
  mID = 0;
}
requestAnimationFrame(manualMouseMove);
