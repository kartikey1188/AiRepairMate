import MainPage from "../pages/MainPage.js";

const routes = [
    {path : '/', component : MainPage},
]

const router = new VueRouter({
    routes
})

export default router;