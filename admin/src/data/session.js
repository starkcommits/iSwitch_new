import router from "@/router"
import { createResource } from "frappe-ui"
import { computed, reactive } from "vue"

import { userResource } from "./user"

export function sessionUser() {
	const cookies = new URLSearchParams(document.cookie.split("; ").join("&"))
	let _sessionUser = cookies.get("user_id")
	if (_sessionUser === "Guest") {
		_sessionUser = null
	}
	return _sessionUser
}

export const session = reactive({
	login: createResource({
		url: "login",
		makeParams({ email, password }) {
			return {
				usr: email,
				pwd: password,
			}
		},
		onSuccess(data) {
			userResource.reload()
			session.user = sessionUser()
			session.login.reset()
			router.replace(data.default_route || "/")
		},
	}),
	logout: createResource({
		url: "logout",
		onSuccess() {
			userResource.reset()
			session.user = sessionUser()
			window.location.href = "/login?redirect-to=%2Fadmin#login"
		},
	}),
	userContext: createResource({
		url: "iswitch.session_api.get_user_context",
		auto: false,
		cache: "UserContext",
	}),
	user: sessionUser(),
	isLoggedIn: computed(() => !!session.user),
	roles: computed(() => session.userContext.data?.roles || []),
	isAdmin: computed(() => session.userContext.data?.is_admin || false),
	isMerchant: computed(() => session.userContext.data?.is_merchant || false),
})
