'use strict';
// Extract generated pigment onto open rock without moving ancestral pixels.
const fs=require('node:fs'), crypto=require('node:crypto');
const {decodePNG,encodePNG,preview}=require('./finish_wall.js');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const old=fs.readFileSync('artifacts/line-1/wall.png');
const previous=JSON.parse(fs.readFileSync('dist/line-1/28.json','utf8'));
if(previous.image!=='https://api.imd.fun/artifacts/'+hash(old)) throw Error('ancestor digest mismatch');
const ancestor=decodePNG('artifacts/line-1/wall.png');
const pigment=decodePNG('artifacts/line-1/wall-v10.png');
const result={...ancestor,pixels:Buffer.from(ancestor.pixels)};
const bounds=[675,856,805,923], source=[370,280,1190,730];
let changed=0;
for(let y=bounds[1];y<bounds[3];y++) for(let x=bounds[0];x<bounds[2];x++) {
  const colors=[0,0,0];
  for(const dy of [.25,.75]) for(const dx of [.25,.75]) {
    const sx=Math.floor(source[0]+(x-bounds[0]+dx)/(bounds[2]-bounds[0])*(source[2]-source[0]));
    const sy=Math.floor(source[1]+(y-bounds[1]+dy)/(bounds[3]-bounds[1])*(source[3]-source[1]));
    for(let c=0;c<3;c++) colors[c]+=pigment.pixels[(sy*pigment.width+sx)*pigment.channels+c]/4;
  }
  const [r,g,b]=colors;
  const black=Math.max(r,g,b)<90;
  const red=r>g*1.5 && r>b*1.8 && g<110;
  const chalk=r>160 && g>150 && b>130 && g-b<27 && r-g<35;
  if(!black&&!red&&!chalk) continue;
  const alpha=black?Math.min(.8,(110-Math.max(r,g,b))/65):red?Math.min(.8,(r-g)/110):.45;
  const color=black?[37,29,18]:red?[133,53,23]:[221,201,158];
  const at=(y*result.width+x)*result.channels;
  for(let c=0;c<3;c++) result.pixels[at+c]=Math.round(ancestor.pixels[at+c]*(1-alpha)+color[c]*alpha);
}
let outside=true;
for(let y=0;y<result.height;y++) for(let x=0;x<result.width;x++) {
  const at=(y*result.width+x)*result.channels;
  const different=!result.pixels.subarray(at,at+result.channels).equals(ancestor.pixels.subarray(at,at+ancestor.channels));
  if(different) {changed++;if(!(x>=bounds[0]&&x<bounds[2]&&y>=bounds[1]&&y<bounds[3]))outside=false;}
}
if(!outside||changed<100)throw Error('failed preservation/empty mark');
const png=encodePNG(result), jpg=preview(result);
if(jpg.length>100000)throw Error('preview exceeds 100 KB');
fs.writeFileSync('artifacts/line-1/wall-v10.png',png);
fs.writeFileSync('artifacts/line-1/wall.png',png);
fs.writeFileSync('dist/line-1/29.jpg',jpg);
const report={bounds,source,changed_pixels:changed,all_pixels_outside_identical:outside,ancestor_sha256:hash(old),wall_sha256:hash(png),width:result.width,height:result.height,format:'PNG RGB8',png_bytes:png.length,preview:{width:512,height:512,format:'JPEG',bytes:jpg.length},generator:'installed mcp image generate_image; pigment extracted from generated insert'};
fs.writeFileSync('line-1/mark-process-29.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
