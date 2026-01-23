import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { CartItem } from '@/lib/types';
import { Button as FluentButton } from '@fluentui/react-components';
import { Minus, Plus, ShoppingCart, X } from '@phosphor-icons/react';

interface CartDrawerProps {
  cartItems: CartItem[];
  onUpdateQuantity: (productId: string, quantity: number) => void;
  onRemoveItem: (productId: string) => void;
  onCheckout: () => void;
  onCartOpen?: () => void;
}

export const CartDrawer = ({ cartItems, onUpdateQuantity, onRemoveItem, onCheckout, onCartOpen }: CartDrawerProps) => {
  // Ensure cartItems is always an array
  const safeCartItems = Array.isArray(cartItems) ? cartItems : [];
  const totalItems = safeCartItems.reduce((sum, item) => sum + item.quantity, 0);
  const totalPrice = safeCartItems.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);

  const CartContent = () => (
    <div className="flex flex-col h-full">
      <div className="flex-1">
        {safeCartItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-center">
            <ShoppingCart className="w-12 h-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Your cart is empty</p>
            <p className="text-sm text-muted-foreground">Add some products to get started</p>
          </div>
        ) : (
          <ScrollArea className="h-full">
            <div className="space-y-4 p-4">
              {safeCartItems.map((item) => (
                <Card key={item.product.id} className="overflow-hidden">
                  <CardContent className="p-4">
                    <div className="flex gap-4">
                      <img
                        src={item.product.image}
                        alt={item.product.title}
                        className="w-16 h-16 object-cover rounded-lg flex-shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-sm leading-tight line-clamp-2 mb-2">
                          {item.product.title}
                        </h4>
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-primary">
                            ${item.product.price}
                          </span>
                          <div className="flex items-center gap-2">
                            <div className="flex items-center border rounded-lg">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onUpdateQuantity(item.product.id, Math.max(0, item.quantity - 1))}
                                className="h-8 w-8 p-0"
                              >
                                <Minus className="h-3 w-3" />
                              </Button>
                              <span className="px-3 py-1 text-sm font-medium min-w-[2rem] text-center">
                                {item.quantity}
                              </span>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => onUpdateQuantity(item.product.id, item.quantity + 1)}
                                className="h-8 w-8 p-0"
                              >
                                <Plus className="h-3 w-3" />
                              </Button>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onRemoveItem(item.product.id)}
                              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        )}
      </div>

      {cartItems.length > 0 && (
        <div className="border-t p-4 space-y-4">
          <div className="flex justify-between items-center">
            <span className="font-semibold">Total: ${totalPrice.toFixed(2)}</span>
            <span className="text-sm text-muted-foreground">
              {totalItems} item{totalItems !== 1 ? 's' : ''}
            </span>
          </div>
          <Button className="w-full" size="lg" onClick={onCheckout}>
            Proceed to Checkout
          </Button>
        </div>
      )}
    </div>
  );

  return (
    <Sheet>
      <SheetTrigger asChild>
        <FluentButton
          appearance="subtle"
          size="small"
          icon={<ShoppingCart className="w-4 h-4" />}
          className="relative transition-all duration-200"
          onClick={() => onCartOpen?.()}
          title="Shopping Cart"
        >
          {totalItems > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              {totalItems > 99 ? '99+' : totalItems}
            </Badge>
          )}
        </FluentButton>
      </SheetTrigger>
      <SheetContent className="w-full sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5" />
            Shopping Cart
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6 h-[calc(100vh-8rem)]">
          <CartContent />
        </div>
      </SheetContent>
    </Sheet>
  );
};