import {reactive} from 'vue'
// const pTitle = ref('')
// const version = ref('')
export const store=reactive({
    pTitle:"",
    token:localStorage.getItem("token") || '',
    level:localStorage.getItem("level") || 'common',
    username:localStorage.getItem("username") || '',
    version:"",
    prompt:'',
    comparisonList:[],
    promptList:[],
    setTitle(title){
        this.pTitle=title
    },
    setToken(token){
        this.token=token
        localStorage.setItem("token",token)
    },
    setLevel(level){
        this.level=level
        localStorage.setItem("level",level)
    },
    setUsername(username){
        this.username=username
        localStorage.setItem("username",username)
    },
    setVersion(version){
      this.version=version
    },
    setPrompt(prompt){
      this.prompt=prompt
    },
    setComparisonList(comparisonList){
      this.comparisonList=comparisonList
    },
    setPromptList(promptList){
      this.promptList=promptList
    },
})