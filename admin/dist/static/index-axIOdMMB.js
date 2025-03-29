import{r as R,_ as Z}from"./index-SlZVGBFr.js";import{p as F,E,s as ne,r as re,q as ue}from"./element-BJhk1yyC.js";import{u as de}from"./usePagination-DRno2DY3.js";import{l as G,r as g,Z as H,ah as t,m as f,M as w,O as l,U as e,S as n,e as ie,b as pe,ap as ce,p as me,P as _e,u as _,q as k,T as j,aE as fe,aF as ge}from"./vue-DSQ7aDT9.js";import"./vxe-Cuv8YH4T.js";function ve(r,m){return R({url:`customer/status/${r}`,method:"post",data:{status:m}})}function be(r){return R({url:`customer/${r.id}`,method:"post",data:r})}function we(r){return R({url:"customers",method:"get",params:r})}function he(r){return R({url:"customer",method:"PUT",data:r})}const ye=G({__name:"register",emits:["success"],setup(r,{emit:m}){const u=m,M={email:"",password:"",level:"common"},c=g(F(M)),x=g(null),v=H({email:[{required:!0,message:"请填写邮箱地址",trigger:"blur"}],level:[{required:!0,message:"请填写用户等级"}],password:[{required:!0,message:"请填写密码",trigger:"blur"}]}),S=()=>{var s;(s=x.value)==null||s.validate((i,V)=>{if(!i)return console.error("表单校验不通过",V);he(c.value).then(()=>{E.success("操作成功"),u("success"),c.value=F(M)}).finally(()=>{})})};return(s,i)=>{const V=t("el-input"),C=t("el-form-item"),U=t("el-option"),q=t("el-select"),z=t("el-button"),$=t("el-form");return f(),w($,{model:c.value,ref_key:"userform",ref:x,"label-width":"auto",rules:v},{default:l(()=>[e(C,{prop:"email",label:"邮箱"},{default:l(()=>[e(V,{modelValue:c.value.email,"onUpdate:modelValue":i[0]||(i[0]=p=>c.value.email=p),placeholder:"请输入邮箱",autocomplete:"new-password"},null,8,["modelValue"])]),_:1}),e(C,{prop:"level",label:"用户等级"},{default:l(()=>[e(q,{modelValue:c.value.level,"onUpdate:modelValue":i[1]||(i[1]=p=>c.value.level=p),placeholder:""},{default:l(()=>[e(U,{label:"会员用户",value:"vip"}),e(U,{label:"普通用户",value:"common"})]),_:1},8,["modelValue"])]),_:1}),e(C,{prop:"password",label:"密码"},{default:l(()=>[e(V,{type:"password",modelValue:c.value.password,"onUpdate:modelValue":i[2]||(i[2]=p=>c.value.password=p),placeholder:"请输入",autocomplete:"new-password"},null,8,["modelValue"])]),_:1}),e(C,{label:"",class:"center"},{default:l(()=>[e(z,{type:"primary",size:"large",color:"#055CF9",onClick:i[3]||(i[3]=p=>S()),style:{width:"100%"}},{default:l(()=>[n("提交")]),_:1})]),_:1})]),_:1},8,["model","rules"])}}}),Ve=Z(ye,[["__scopeId","data-v-e1b2fb46"]]),Ce=r=>(fe("data-v-84b0f559"),r=r(),ge(),r),ke={class:"app-container"},xe={class:"table-wrapper"},Se={class:"pager-wrapper"},Ue={class:"dialog_head"},ze={class:"title"},De=Ce(()=>k("span",{class:"ml-2"},"MB",-1)),Pe={class:"btn_box"},Fe=G({name:"ElementPlus",__name:"index",setup(r){const m=g(!1),{paginationData:u,handleCurrentChange:M,handleSizeChange:c}=de(),x={id:void 0,email:"",password:"",level:"common",add_storage:0},v=g(!1),S=g(null),s=g(F(x)),i={email:[{required:!0,trigger:"blur",message:"请输入注册邮箱"}],password:[{min:6,max:16,message:"长度在 6 到 16 个字符",trigger:"blur"}],level:[{required:!0,trigger:"blur",message:"请选择用户等级"}]},V=()=>{var d;(d=S.value)==null||d.validate((o,P)=>{if(!o)return console.error("表单校验不通过",P);m.value=!0,be(s.value).then(()=>{E.success("操作成功"),v.value=!1,D()}).finally(()=>{m.value=!1})})},C=()=>{var d;(d=S.value)==null||d.clearValidate(),s.value=F(x),v.value=!1},U=(d,o)=>{ve(d,o).then(()=>{E.success("更改状态成功"),D()})},q=d=>{v.value=!0,s.value=Object.assign(F(d),{password:""})},z=g([]),$=g(null),p=H({keyword:""}),D=()=>{m.value=!0,we({page:u.currentPage,limit:u.pageSize,keyword:p.keyword||void 0}).then(({data:d})=>{u.total=d.total,z.value=d.data}).catch(()=>{z.value=[]}).finally(()=>{m.value=!1})},T=()=>{u.currentPage===1?D():u.currentPage=1},J=()=>{p.keyword="",T()},A=g(!1),K=()=>{A.value=!0},Q=()=>{A.value=!1,D()},W=ie(()=>Math.floor(s.value.storage/(1024*1024)));return pe([()=>u.currentPage,()=>u.pageSize],D,{immediate:!0}),(d,o)=>{const P=t("el-input"),h=t("el-form-item"),b=t("el-button"),I=t("el-form"),y=t("el-table-column"),B=t("el-tag"),X=t("el-table"),Y=t("el-pagination"),ee=t("el-card"),le=t("Close"),ae=t("el-icon"),O=t("el-option"),te=t("el-select"),oe=t("el-input-number"),N=t("el-dialog"),se=ce("loading");return f(),me("div",ke,[_e((f(),w(ee,{shadow:"never"},{default:l(()=>[e(I,{ref_key:"searchFormRef",ref:$,inline:!0,model:p},{default:l(()=>[e(h,{prop:"username",label:"",style:{width:"320px","max-width":"100%"}},{default:l(()=>[e(P,{modelValue:p.keyword,"onUpdate:modelValue":o[0]||(o[0]=a=>p.keyword=a),placeholder:"输入查询"},null,8,["modelValue"])]),_:1}),e(h,null,{default:l(()=>[e(b,{type:"primary",icon:_(ne),onClick:T},{default:l(()=>[n("查询")]),_:1},8,["icon"]),e(b,{icon:_(re),onClick:J},{default:l(()=>[n("重置")]),_:1},8,["icon"])]),_:1}),e(h,null,{default:l(()=>[e(b,{type:"primary",icon:_(ue),onClick:K},{default:l(()=>[n("新增用户")]),_:1},8,["icon"])]),_:1})]),_:1},8,["model"]),k("div",xe,[e(X,{data:z.value},{default:l(()=>[e(y,{prop:"customer_no",label:"用户编号",align:"left"}),e(y,{prop:"email",label:"注册邮箱",align:"left"}),e(y,{prop:"level",label:"用户等级",align:"left"},{default:l(a=>[a.row.level=="vip"?(f(),w(B,{key:0,type:"primary",effect:"plain"},{default:l(()=>[n("会员用户")]),_:1})):(f(),w(B,{key:1,type:"warning",effect:"plain"},{default:l(()=>[n("普通用户")]),_:1}))]),_:1}),e(y,{prop:"storage",label:"已用存储空间",align:"left"},{default:l(({row:a})=>[n(j((a.storage/(1024*1024)).toFixed(2))+" MB ",1)]),_:1}),e(y,{prop:"status",label:"账户状态",align:"left"},{default:l(a=>[a.row.status=="enabled"?(f(),w(B,{key:0,type:"success",effect:"plain"},{default:l(()=>[n("启用")]),_:1})):(f(),w(B,{key:1,type:"danger",effect:"plain"},{default:l(()=>[n("禁用")]),_:1}))]),_:1}),e(y,{prop:"created_at",label:"注册时间",align:"left"}),e(y,{fixed:"right",label:"操作",width:"100",align:"left"},{default:l(a=>[e(b,{type:"primary",text:"",size:"small",onClick:L=>q(a.row)},{default:l(()=>[n("编辑")]),_:2},1032,["onClick"]),a.row.status=="enabled"?(f(),w(b,{key:0,type:"danger",text:"",size:"small",onClick:L=>U(a.row.id,"disabled")},{default:l(()=>[n("禁用")]),_:2},1032,["onClick"])):(f(),w(b,{key:1,type:"success",text:"",size:"small",onClick:L=>U(a.row.id,"enabled")},{default:l(()=>[n("启用")]),_:2},1032,["onClick"]))]),_:1})]),_:1},8,["data"])]),k("div",Se,[e(Y,{background:"",layout:_(u).layout,"page-sizes":_(u).pageSizes,total:_(u).total,"page-size":_(u).pageSize,currentPage:_(u).currentPage,onSizeChange:_(c),onCurrentChange:_(M)},null,8,["layout","page-sizes","total","page-size","currentPage","onSizeChange","onCurrentChange"])])]),_:1})),[[se,m.value]]),e(N,{"modal-class":"custom_dialog",modelValue:v.value,"onUpdate:modelValue":o[6]||(o[6]=a=>v.value=a),"show-close":!1},{header:l(()=>[k("div",Ue,[k("div",ze,j(s.value.id===void 0?"新增用户":"编辑用户信息"),1),e(ae,{onClick:C},{default:l(()=>[e(le)]),_:1})])]),default:l(()=>[e(I,{ref_key:"formRef",ref:S,model:s.value,rules:i,"label-width":"150px","label-position":"left"},{default:l(()=>[e(h,{prop:"email",label:"注册邮箱"},{default:l(()=>[e(P,{modelValue:s.value.email,"onUpdate:modelValue":o[1]||(o[1]=a=>s.value.email=a),placeholder:"请输入注册邮箱"},null,8,["modelValue"])]),_:1}),e(h,{prop:"level",label:"用户等级"},{default:l(()=>[e(te,{modelValue:s.value.level,"onUpdate:modelValue":o[2]||(o[2]=a=>s.value.level=a),placeholder:""},{default:l(()=>[e(O,{label:"会员用户",value:"vip"}),e(O,{label:"普通用户",value:"common"})]),_:1},8,["modelValue"])]),_:1}),e(h,{prop:"storage",label:"新增存储空间(MB)"},{default:l(()=>[e(oe,{style:{width:"80%"},precision:0,modelValue:s.value.add_storage,"onUpdate:modelValue":o[3]||(o[3]=a=>s.value.add_storage=a),max:W.value,step:5,placeholder:"请输入需要添加的存储空间(MB)"},null,8,["modelValue","max"]),De]),_:1}),e(h,{prop:"password",label:"密码"},{default:l(()=>[e(P,{type:"password",modelValue:s.value.password,"onUpdate:modelValue":o[4]||(o[4]=a=>s.value.password=a),placeholder:"请输入"},null,8,["modelValue"])]),_:1})]),_:1},8,["model"]),k("div",Pe,[e(b,{onClick:o[5]||(o[5]=a=>v.value=!1)},{default:l(()=>[n("取消")]),_:1}),e(b,{type:"primary",onClick:V,loading:m.value},{default:l(()=>[n("确认")]),_:1},8,["loading"])])]),_:1},8,["modelValue"]),e(N,{modelValue:A.value,"onUpdate:modelValue":o[7]||(o[7]=a=>A.value=a),center:"",width:"90%","modal-class":"custom_dialog login_dialog","show-close":!1},{header:l(()=>[n(" 添加用户 ")]),default:l(()=>[e(Ve,{onSuccess:Q})]),_:1},8,["modelValue"])])}}}),$e=Z(Fe,[["__scopeId","data-v-84b0f559"]]);export{$e as default};
