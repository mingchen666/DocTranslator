//引入mitt插件:mitt一个方法,方法执行会返回bus对象
import mitt from 'mitt';
const $bus = mitt();
export default $bus;