import CategoryShopLayout from '../_components/CategoryShopLayout';
import { FURNITURE_CONFIG } from '../_config/categories';

export const metadata = { title: 'Furniture — Hanna Shop' };

export default function FurniturePage() {
  return <CategoryShopLayout config={FURNITURE_CONFIG} />;
}
