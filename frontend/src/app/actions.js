"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { ApiError } from "@/lib/api";
import {
  UnauthenticatedError,
  addCartItem,
  cancelOrder,
  clearCart,
  ensureCsrfCookie,
  login,
  logout,
  placeOrder,
  register,
  removeCartItem,
  updateCartItem,
} from "@/lib/serverApi";

/**
 * Server Actions for every write.
 *
 * Each one forwards Django's CSRF cookie to the browser first, then performs
 * the unsafe request with that token. Failures are returned as plain data for
 * `useActionState`; they never leak a stack trace to the client.
 */

function asErrorMessage(error, fallback) {
  if (error instanceof ApiError) return error.message || fallback;
  if (error instanceof UnauthenticatedError) {
    return "Your session has expired. Please sign in again.";
  }
  return fallback;
}

export async function loginAction(_prevState, formData) {
  const username = String(formData.get("username") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!username || !password) {
    return { error: "Enter your username and password.", fields: {} };
  }

  try {
    await ensureCsrfCookie();
    await login({ username, password });
  } catch (error) {
    return {
      error: asErrorMessage(error, "Could not sign you in."),
      fields: {},
    };
  }

  revalidatePath("/", "layout");
  // Only accept a relative path so this can never become an open redirect.
  redirect("/");
}

export async function registerAction(_prevState, formData) {
  const username = String(formData.get("username") ?? "").trim();
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const confirm = String(formData.get("confirm_password") ?? "");

  if (!username || !email || !password) {
    return {
      error: "Fill in every field.",
      fields: {},
    };
  }
  if (password !== confirm) {
    return { error: "The passwords do not match.", fields: {} };
  }

  try {
    await ensureCsrfCookie();
    await register({ username, email, password });
  } catch (error) {
    if (error instanceof ApiError) {
      return {
        error: "Please correct the highlighted fields.",
        fields: error.fieldErrors,
      };
    }
    return { error: asErrorMessage(error, "Could not create your account."), fields: {} };
  }

  revalidatePath("/", "layout");
  redirect("/");
}

export async function logoutAction() {
  try {
    await ensureCsrfCookie();
    await logout();
  } catch {
    // Signing out locally must succeed even if Django already dropped it.
  }
  revalidatePath("/", "layout");
  redirect("/");
}

export async function addToCartAction(_prevState, formData) {
  const productId = Number(formData.get("product_id"));
  const quantity = Math.max(1, Number(formData.get("quantity") ?? 1));

  if (!Number.isInteger(productId) || productId <= 0) {
    return { error: "That product could not be added." };
  }

  try {
    await ensureCsrfCookie();
    await addCartItem({ productId, quantity });
  } catch (error) {
    if (error instanceof UnauthenticatedError) {
      return { error: "Sign in to add items to your cart." };
    }
    if (error instanceof ApiError) {
      const fields = error.fieldErrors;
      return {
        error: fields.quantity ?? error.message ?? "Could not add to your cart.",
      };
    }
    return { error: "Could not add to your cart." };
  }

  revalidatePath("/cart");
  revalidatePath("/", "layout");
  return { success: "Added to your cart." };
}

export async function updateCartItemAction(_prevState, formData) {
  const itemId = Number(formData.get("item_id"));
  const quantity = Number(formData.get("quantity"));

  try {
    await ensureCsrfCookie();
    await updateCartItem(itemId, { quantity });
  } catch (error) {
    if (error instanceof UnauthenticatedError) {
      return { error: "Your session has expired. Please sign in again." };
    }
    if (error instanceof ApiError) {
      const fields = error.fieldErrors;
      return { error: fields.quantity ?? error.message ?? "Could not update." };
    }
    return { error: "Could not update that item." };
  }

  revalidatePath("/cart");
  revalidatePath("/checkout");
  revalidatePath("/", "layout");
  return { success: true };
}

export async function removeCartItemAction(formData) {
  const itemId = Number(formData.get("item_id"));

  try {
    await ensureCsrfCookie();
    await removeCartItem(itemId);
  } catch {
    // Treat a failure as "still in the cart" and let the revalidation show it.
  }

  revalidatePath("/cart");
  revalidatePath("/checkout");
  revalidatePath("/", "layout");
}

export async function clearCartAction() {
  try {
    await ensureCsrfCookie();
    await clearCart();
  } catch {
    // Nothing to recover: the revalidated cart reflects the server state.
  }
  revalidatePath("/cart");
  revalidatePath("/checkout");
  revalidatePath("/", "layout");
}

export async function placeOrderAction(_prevState, formData) {
  try {
    await ensureCsrfCookie();
    const order = await placeOrder();
    revalidatePath("/cart");
    revalidatePath("/orders");
    revalidatePath("/", "layout");
    return { success: true, orderId: order.id };
  } catch (error) {
    if (error instanceof UnauthenticatedError) {
      return { error: "Sign in to place an order." };
    }
    if (error instanceof ApiError) {
      return { error: error.message ?? "Could not place your order." };
    }
    return { error: "Could not place your order." };
  }
}

export async function cancelOrderAction(formData) {
  const orderId = Number(formData.get("order_id"));

  try {
    await ensureCsrfCookie();
    await cancelOrder(orderId);
  } catch {
    // The revalidated order will show its real status.
  }

  revalidatePath("/orders");
  revalidatePath(`/orders/${orderId}`);
  revalidatePath("/", "layout");
}
