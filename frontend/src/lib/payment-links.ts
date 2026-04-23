import type { PaymentLinks } from "@/lib/types";

export function getPaymentLinks(): PaymentLinks {
  return {
    stripe: process.env.STRIPE_PAYMENT_URL || "https://buy.stripe.com/cNibJ2feR8nx0lodvE2go0b",
    paypal: process.env.PAYPAL_PAYMENT_URL || "https://paypal.me/etherealrest",
    telegramStarsPlaceholder: "Telegram Stars integration is coming soon"
  };
}
