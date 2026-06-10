import CategoryShopLayout from '../../_components/CategoryShopLayout';
import { FURNITURE_KITCHEN_CONFIG } from '../../_config/categories';

export const metadata = { title: 'Kitchen Furniture — Hanna Shop' };

export default function KitchenFurniturePage() {
  return <CategoryShopLayout config={FURNITURE_KITCHEN_CONFIG} />;
}
