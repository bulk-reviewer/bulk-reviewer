import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'landing-page',
      component: require('@/components/LandingPage').default
    },
    {
      path: '/review',
      name: 'review-dashboard',
      component: require('@/components/ReviewDashboard').default
    },
    {
      path: '/new-session',
      name: 'new-session',
      component: require('@/components/NewSession').default
    },
    {
      path: '*',
      redirect: '/'
    }
  ]
})
