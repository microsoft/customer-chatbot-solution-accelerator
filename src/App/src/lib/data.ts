import { Product, SortBy } from './types';


export const sortOptions = [
  { value: 'name', label: 'Name (A-Z)' },
  { value: 'price-asc', label: 'Price: Low to High' },
  { value: 'price-desc', label: 'Price: High to Low' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'newest', label: 'Newest First' }
];

export const categories = ['All', 'Electronics', 'Furniture', 'Kitchen', 'Lighting', 'Plants', 'Accessories'];

export function sortProducts(products: Product[], sortBy: SortBy): Product[] {
  return [...products].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.title.localeCompare(b.title);
      case 'price-asc':
        return a.price - b.price;
      case 'price-desc':
        return b.price - a.price;
      case 'rating':
        return b.rating - a.rating;
      case 'newest':
        return b.id.localeCompare(a.id); // Assuming higher IDs are newer
      default:
        return 0;
    }
  });
}

export function filterProducts(products: Product[], searchQuery: string, filters: any): Product[] {
  return products.filter(product => {
    const matchesSearch = product.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         product.category.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = filters.category === 'All' || product.category === filters.category;
    const matchesPrice = product.price >= filters.minPrice && product.price <= filters.maxPrice;
    const matchesRating = product.rating >= filters.minRating;
    const matchesStock = !filters.inStockOnly || product.inStock;

    return matchesSearch && matchesCategory && matchesPrice && matchesRating && matchesStock;
  });
}