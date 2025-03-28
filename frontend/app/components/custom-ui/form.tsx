import { Slot } from '@radix-ui/react-slot';
import { createFormHook, createFormHookContexts } from '@tanstack/react-form';
import type { VariantProps } from 'class-variance-authority';
import { MapPinIcon, XIcon } from 'lucide-react';
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import type { MarkerDragEvent } from 'react-map-gl/maplibre';
import { Marker } from 'react-map-gl/maplibre';

import { BaseMap } from '@/components/custom-ui/base-map';
import { Spinner } from '@/components/custom-ui/spinner';
import { Button, type buttonVariants } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

import { cn } from '@/lib/utils';

const { fieldContext, useFieldContext, formContext, useFormContext } =
  createFormHookContexts();

type BaseFieldProps = {
  className?: string;
  label: string;
  children: React.ReactNode;
};

function BaseField({ className, label, children }: BaseFieldProps) {
  const field = useFieldContext();
  const id = useId();

  return (
    <div className={cn('realtive space-y-2', className)}>
      <Label
        className={cn(field.state.meta.errors.length > 0 && 'text-destructive')}
        htmlFor={`${id}-form-item`}
      >
        {label}
      </Label>
      <Slot
        id={`${id}-form-item`}
        aria-describedby={
          !(field.state.meta.errors.length > 0)
            ? `${id}-form-item-description`
            : `${id}-form-item-description ${id}-form-item-message`
        }
        aria-invalid={!!(field.state.meta.errors.length > 0)}
      >
        {children}
      </Slot>
      <p
        id={`${id}-form-item-description`}
        className={cn('text-muted-foreground text-sm', className)}
      />
      <p
        id={`${id}-form-item-message`}
        className={cn(
          'text-destructive absolute -translate-y-2 text-[0.8rem] font-medium',
          className,
        )}
      >
        {field.state.meta.errors.length > 0 &&
          (field.state.meta.errors[0] as { message: string }).message}
      </p>
    </div>
  );
}

type TextFieldProps = Omit<
  React.ComponentProps<typeof Input>,
  'type' | 'value' | 'onChange' | 'onBlur'
> & {
  label: string;
};

function TextField({ className, label, ...props }: TextFieldProps) {
  const field = useFieldContext<string>();

  return (
    <BaseField label={label} className={className}>
      <Input
        type='text'
        value={field.state.value}
        onChange={(e) => field.handleChange(e.target.value)}
        onBlur={field.handleBlur}
        {...props}
      />
    </BaseField>
  );
}

type NumberFieldProps = Omit<
  React.ComponentProps<typeof Input>,
  'type' | 'value' | 'onChange' | 'onBlur'
> & {
  label: string;
};

function NumberField({ className, label, ...props }: NumberFieldProps) {
  const field = useFieldContext<number>();

  return (
    <BaseField label={label} className={className}>
      <Input
        type='number'
        value={field.state.value}
        onChange={(e) => field.handleChange(Number(e.target.value))}
        onBlur={field.handleBlur}
        {...props}
      />
    </BaseField>
  );
}

type TextAreaFieldProps = Omit<
  React.ComponentProps<typeof Textarea>,
  'value' | 'onChange' | 'onBlur'
> & {
  label: string;
};

function TextAreaField({ className, label, ...props }: TextAreaFieldProps) {
  const field = useFieldContext<string>();

  return (
    <BaseField label={label} className={className}>
      <Textarea
        value={field.state.value}
        onChange={(e) => field.handleChange(e.target.value)}
        onBlur={field.handleBlur}
        {...props}
      />
    </BaseField>
  );
}

type Location = {
  longitude: number;
  latitude: number;
};

type MapFieldProps = {
  label: string;
  className?: string;
  zoom?: number;
  coordinates?: Location;
};

const DEFAULT_COORDINATES: Location = {
  longitude: 0,
  latitude: 0,
} as const;

function MapField({
  label,
  className,
  zoom = 4,
  coordinates = DEFAULT_COORDINATES,
}: MapFieldProps) {
  const field = useFieldContext<Location>();

  const onMarkerDrag = useCallback(
    (event: MarkerDragEvent) => {
      field.handleChange({
        longitude: event.lngLat.lng,
        latitude: event.lngLat.lat,
      });
    },
    [field],
  );

  return (
    <BaseField label={label} className={className}>
      <div className='h-[400px] w-full rounded-md border'>
        <BaseMap
          initialViewState={{
            zoom,
            longitude: coordinates.longitude,
            latitude: coordinates.latitude,
          }}
        >
          <Marker
            longitude={field.state.value?.longitude ?? coordinates.longitude}
            latitude={field.state.value?.latitude ?? coordinates.latitude}
            anchor='bottom'
            draggable
            onDrag={onMarkerDrag}
          >
            <MapPinIcon className='text-primary h-8 w-8 -translate-y-full hover:scale-120' />
          </Marker>
        </BaseMap>
      </div>
    </BaseField>
  );
}

type CurrencyFieldProps = Omit<
  React.ComponentProps<typeof Input>,
  'type' | 'value' | 'onChange' | 'onBlur'
> & {
  label: string;
  currency?: string;
  locale?: string;
};

function CurrencyField({
  className,
  label,
  currency = 'NOK',
  locale = 'nb-NO',
  ...props
}: CurrencyFieldProps) {
  const field = useFieldContext<number>();
  const [displayValue, setDisplayValue] = useState(() =>
    field.state.value ? formatCurrency(field.state.value) : '',
  );
  const inputRef = useRef<HTMLInputElement>(null);

  const formatCurrency = useCallback(
    (value: number) => {
      if (isNaN(value) || value === null) return '';
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(value);
    },
    [currency, locale],
  );

  const parseNumber = useCallback((value: string) => {
    const normalizedValue = value.replace(/,/g, '.');
    const cleanValue = normalizedValue.replace(/[^0-9.-]/g, '');
    return cleanValue ? Number(cleanValue) : 0;
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const rawValue = e.target.value;
      setDisplayValue(rawValue);
      const numericValue = parseNumber(rawValue);
      field.handleChange(numericValue);
    },
    [field, parseNumber],
  );

  const handleFocus = useCallback(() => {
    const numericValue = field.state.value ?? 0;
    setDisplayValue(numericValue.toString());
  }, [field.state.value]);

  const handleBlur = useCallback(() => {
    field.handleBlur();
    const currentValue = field.state.value ?? 0;
    setDisplayValue(formatCurrency(currentValue));
  }, [field, formatCurrency]);

  useEffect(() => {
    if (document.activeElement !== inputRef.current) {
      requestAnimationFrame(() => {
        setDisplayValue(
          field.state.value ? formatCurrency(field.state.value) : '',
        );
      });
    }
  }, [field.state.value, formatCurrency]);

  return (
    <BaseField label={label} className={className}>
      <Input
        ref={inputRef}
        type='text'
        value={displayValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={`0,00 ${currency}`}
        {...props}
      />
    </BaseField>
  );
}

type SelectOption = {
  label: string;
  value: string;
};

type SelectFieldProps = {
  label: string;
  className?: string;
  placeholder?: string;
  options: SelectOption[];
  required?: boolean;
};

function SelectField({
  label,
  className,
  placeholder = 'Select an option',
  options,
  required = true,
}: SelectFieldProps) {
  const field = useFieldContext<string>();

  return (
    <BaseField label={label} className={className}>
      <div className='flex gap-2'>
        <Select
          value={field.state.value ?? undefined}
          onValueChange={field.handleChange}
          required={required}
        >
          <SelectTrigger className='w-full'>
            <SelectValue placeholder={placeholder} />
          </SelectTrigger>
          <SelectContent>
            {options.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {!required && field.state.value && (
          <Button
            type='button'
            variant='outline'
            size='icon'
            onClick={() => field.handleChange('')}
          >
            <XIcon className='h-4 w-4' />
          </Button>
        )}
      </div>
    </BaseField>
  );
}

type SubmitButtonProps = Omit<React.ComponentProps<typeof Button>, 'type'> &
  VariantProps<typeof buttonVariants> & {
    loading?: boolean;
  };

function SubmitButton({
  children,
  className,
  loading,
  ...props
}: SubmitButtonProps) {
  const form = useFormContext();
  return (
    <form.Subscribe
      selector={(state) => [
        state.isSubmitting,
        state.isPristine,
        state.isValidating,
      ]}
    >
      {([isSubmitting, isPristine, isValidating]) => (
        <Button
          className={cn('min-w-28', className)}
          type='submit'
          disabled={isSubmitting ?? isPristine ?? isValidating ?? loading}
          {...props}
        >
          {isSubmitting || isValidating || loading ? (
            <Spinner size='sm' />
          ) : (
            children
          )}
        </Button>
      )}
    </form.Subscribe>
  );
}

const { useAppForm } = createFormHook({
  fieldComponents: {
    TextField,
    NumberField,
    TextAreaField,
    MapField,
    CurrencyField,
    SelectField,
  },
  formComponents: {
    SubmitButton,
  },
  fieldContext,
  formContext,
});

export { useAppForm };
