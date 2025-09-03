import axios from 'axios';
import type { AxiosInstance } from 'axios';

// API Base URL - adjust if your backend is running on a different port
const API_BASE_URL = 'http://localhost:8000';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      withCredentials: true, // Important for cookie-based auth
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to handle auth
    this.client.interceptors.request.use(
      (config) => {
        // Add any additional headers if needed
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          console.error('Unauthorized access');
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: { username: string; password: string }) {
    return this.client.post('/auth/login', credentials);
  }

  async register(userData: { username: string; email: string; password: string }) {
    return this.client.post('/auth/register', userData);
  }

  async logout() {
    return this.client.post('/auth/logout');
  }

  async getCurrentUser() {
    return this.client.get('/users/me');
  }

  // Shopping Lists endpoints
  async getShoppingLists(params?: { skip?: number; limit?: number }) {
    return this.client.get('/lists', { params });
  }

  async createShoppingList(listData: { title: string; description?: string }) {
    return this.client.post('/lists', listData);
  }

  async getShoppingList(listId: number) {
    return this.client.get(`/lists/${listId}`);
  }

  async updateShoppingList(listId: number, listData: { title?: string; description?: string }) {
    return this.client.put(`/lists/${listId}`, listData);
  }

  async deleteShoppingList(listId: number) {
    return this.client.delete(`/lists/${listId}`);
  }

  // List Items endpoints
  async getListItems(listId: number) {
    return this.client.get(`/lists/${listId}/items`);
  }

  async createListItem(listId: number, itemData: { name: string; quantity?: number; unit?: string; is_completed?: boolean }) {
    return this.client.post(`/lists/${listId}/items`, itemData);
  }

  async updateListItem(listId: number, itemId: number, itemData: { name?: string; quantity?: number; unit?: string; is_completed?: boolean }) {
    return this.client.put(`/lists/${listId}/items/${itemId}`, itemData);
  }

  async deleteListItem(listId: number, itemId: number) {
    return this.client.delete(`/lists/${listId}/items/${itemId}`);
  }

  // Filters endpoints
  async getFilters() {
    return this.client.get('/filters');
  }

  async createFilter(filterData: { name: string; criteria: string; is_active?: boolean }) {
    return this.client.post('/filters', filterData);
  }

  async updateFilter(filterId: number, filterData: { name?: string; criteria?: string; is_active?: boolean }) {
    return this.client.put(`/filters/${filterId}`, filterData);
  }

  async deleteFilter(filterId: number) {
    return this.client.delete(`/filters/${filterId}`);
  }

  // Discounts endpoints
  async getDiscounts(params?: { skip?: number; limit?: number; store?: string }) {
    return this.client.get('/discounts', { params });
  }

  async createDiscount(discountData: {
    title: string;
    description?: string;
    store: string;
    original_price?: number;
    discount_price?: number;
    discount_percentage?: number;
    valid_until?: string;
    url?: string;
    image_url?: string;
  }) {
    return this.client.post('/discounts', discountData);
  }

  async getDiscount(discountId: number) {
    return this.client.get(`/discounts/${discountId}`);
  }

  async updateDiscount(discountId: number, discountData: {
    title?: string;
    description?: string;
    store?: string;
    original_price?: number;
    discount_price?: number;
    discount_percentage?: number;
    valid_until?: string;
    url?: string;
    image_url?: string;
  }) {
    return this.client.put(`/discounts/${discountId}`, discountData);
  }

  async deleteDiscount(discountId: number) {
    return this.client.delete(`/discounts/${discountId}`);
  }

  // Notifications endpoints
  async getNotifications(params?: { skip?: number; limit?: number; unread_only?: boolean }) {
    return this.client.get('/notifications', { params });
  }

  async createNotification(notificationData: { title: string; message: string; type: string; discount_id?: number }) {
    return this.client.post('/notifications', notificationData);
  }

  async getNotification(notificationId: number) {
    return this.client.get(`/notifications/${notificationId}`);
  }

  async markNotificationRead(notificationId: number) {
    return this.client.put(`/notifications/${notificationId}/read`);
  }

  async deleteNotification(notificationId: number) {
    return this.client.delete(`/notifications/${notificationId}`);
  }
}

// Export a singleton instance
export const apiClient = new ApiClient();
export default apiClient;