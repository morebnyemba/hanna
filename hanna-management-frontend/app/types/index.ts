export interface Product {
  id?: number;
  name: string;
  sku: string;
  description: string;
  price: string;
  product_type: string;
}

export interface WarrantyClaim {
  claim_id: string;
  product_name: string;
  product_serial_number: string;
  customer_name: string;
  status: string;
  created_at: string;
}

export interface JobCard {
  job_card_number: string;
  customer_name: string;
  customer_whatsapp: string;
  serialized_item?: {
    product_name: string;
    serial_number: string;
  };
  status: string;
  creation_date: string;
}
