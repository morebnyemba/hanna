import CategoryShopLayout from '../../_components/CategoryShopLayout';
import { FURNITURE_BEDROOM_CONFIG } from '../../_config/categories';

export const metadata = { title: 'Bedroom Furniture — Hanna Shop' };

export default function BedroomFurniturePage() {
  return <CategoryShopLayout config={FURNITURE_BEDROOM_CONFIG} />;
}
