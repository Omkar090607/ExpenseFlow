if(!matchMedia("(prefers-reduced-motion: reduce)").matches&&matchMedia("(hover:hover)").matches){
document.querySelectorAll(".tilt").forEach(el=>{
el.addEventListener("mousemove",e=>{const r=el.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;el.style.transform=`perspective(800px) rotateY(${x*10}deg) rotateX(${-y*10}deg) translateZ(8px)`});
el.addEventListener("mouseleave",()=>el.style.transform="")})}
