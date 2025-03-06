import router from "./utils/router.js"

const app = new Vue({
    el : '#app',
    template : `
        <div> 

        <div class="container mt-1">
        <div class="card">
        <h3 class="text-success text-center">AI Repair Agent</h3>
        </div>
        </div>

        <router-view> </router-view>
        
        </div>
    `,
    router
})

console.log('The app is on :)')
