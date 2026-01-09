/**
 * API Client Module
 * - RESTful API 호출 관리
 * - 에러 핸들링
 * - 로딩 상태 관리
 */

class ApiClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    /**
     * GET 요청
     */
    async get(endpoint, options = {}) {
        return this._request('GET', endpoint, null, options);
    }

    /**
     * POST 요청
     */
    async post(endpoint, data, options = {}) {
        return this._request('POST', endpoint, data, options);
    }

    /**
     * PUT 요청
     */
    async put(endpoint, data, options = {}) {
        return this._request('PUT', endpoint, data, options);
    }

    /**
     * DELETE 요청
     */
    async delete(endpoint, options = {}) {
        return this._request('DELETE', endpoint, null, options);
    }

    /**
     * 내부 요청 메서드
     */
    async _request(method, endpoint, data = null, options = {}) {
        const url = this.baseURL + endpoint;

        // 인증 토큰 자동 추가
        const token = localStorage.getItem('access_token');
        const headers = { ...this.defaultHeaders };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            method,
            headers: { ...headers, ...options.headers }
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const error = await this._handleError(response);
                throw error;
            }

            // No Content 응답 처리
            if (response.status === 204) {
                return null;
            }

            return await response.json();
        } catch (error) {
            console.error(`[API Error] ${method} ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * 에러 처리
     */
    async _handleError(response) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMessage = typeof errorData.detail === 'string'
                    ? errorData.detail
                    : JSON.stringify(errorData.detail);
            } else if (errorData.message) {
                errorMessage = errorData.message;
            }
        } catch (e) {
            // JSON 파싱 실패 시 기본 메시지 사용
        }

        return new Error(errorMessage);
    }

    /**
     * Query Parameter 빌더
     */
    buildQueryString(params) {
        const query = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                query.append(key, value);
            }
        });

        const queryString = query.toString();
        return queryString ? `?${queryString}` : '';
    }
}

// 전역 인스턴스 생성
const api = new ApiClient();
